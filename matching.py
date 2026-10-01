"""Motor de recomendación de SucesIA: reglas deterministas y explicables.

Índice de idoneidad (0-100) = wA*A + wD*D + wP*P + wT*T
  A  Ajuste competencial = 100 * suma(peso_c * min(nivel_c / requerido_c, 1))
  D  Desempeño           = 100 * (media de la valoración de los dos años - 1) / 4
  P  Potencial           = 100 * (potencial - 1) / 2
  T  Evolución           = 100 * clip(media(nivel_último - nivel_anterior) + 0,5, 0, 1)
La edad NO interviene en la puntuación.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd

PESOS_POR_DEFECTO = {"A": 0.5, "D": 0.2, "P": 0.2, "T": 0.1}
NOMBRES_COMPONENTES = {"A": "Ajuste competencial", "D": "Desempeño", "P": "Potencial", "T": "Evolución"}
DESEMPENO_MINIMO = 3


def redondear(valor: float, decimales: int = 1) -> float:
    """Redondeo 'half up' (89,45 -> 89,5), robusto a errores de coma flotante."""
    d = Decimal(repr(round(float(valor), 9)))
    return float(d.quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_UP))


def normalizar_pesos(pesos: dict[str, float] | None) -> dict[str, float]:
    pesos = dict(PESOS_POR_DEFECTO if pesos is None else pesos)
    total = sum(pesos.values())
    return dict(PESOS_POR_DEFECTO) if total <= 0 else {k: v / total for k, v in pesos.items()}


def preparacion(ajuste: float, brechas: list[dict]) -> str:
    grandes = sum(1 for b in brechas if b["gap"] >= 2)
    if ajuste >= 90 and grandes == 0:
        return "Listo ahora"
    if ajuste >= 75 and grandes <= 1:
        return "1-2 años"
    return "3+ años"


def calcular_ranking(
    plantilla: pd.DataFrame,
    anterior: pd.DataFrame,
    ultimo: pd.DataFrame,
    perfil: pd.DataFrame,
    id_saliente: str,
    pesos: dict[str, float] | None = None,
    jubilacion_candidatos: dict[str, float] | None = None,
    area_puesto: str = "",
    anios_aviso: float = 5,
    niveles_puesto: dict[str, float] | None = None,
    nivel_objetivo: float | None = None,
) -> dict:
    """Calcula el ranking de relevo para el puesto definido en `perfil`.

    perfil: columnas codigo, competencia, nivel_requerido, peso.
    jubilacion_candidatos: id -> años que le faltan para jubilarse (solo para avisar).
    niveles_puesto / nivel_objetivo: nivel jerárquico de cada puesto según el organigrama (1 = el más alto).
      Solo pueden ser relevo las personas de un nivel inferior al del puesto que se cubre
      (en los puestos del nivel más bajo también las del mismo nivel).
    """
    pesos = normalizar_pesos(pesos)
    emp = plantilla.set_index("id_empleado")
    perfil = perfil.copy()
    perfil["peso"] = pd.to_numeric(perfil["peso"], errors="coerce").fillna(0).astype(float)
    perfil["nivel_requerido"] = pd.to_numeric(perfil["nivel_requerido"], errors="coerce").fillna(1).clip(1, 5)
    if perfil["peso"].sum() <= 0:
        raise ValueError("Los pesos del perfil del puesto deben sumar más de 0.")
    perfil["peso"] = perfil["peso"] / perfil["peso"].sum()
    codigos = perfil["codigo"].tolist()
    req = dict(zip(codigos, perfil["nivel_requerido"]))
    peso = dict(zip(codigos, perfil["peso"]))
    nombre = dict(zip(codigos, perfil["competencia"]))
    jubilacion_candidatos = jubilacion_candidatos or {}
    niveles_puesto = niveles_puesto or {}
    validos = [v for v in niveles_puesto.values() if pd.notna(v)]
    es_nivel_base = bool(validos) and nivel_objetivo is not None and nivel_objetivo >= max(validos)

    filas, todas_brechas, todos_niveles = [], {}, {}
    for eid, r in ultimo.iterrows():
        if eid == id_saliente or eid not in emp.index:
            continue
        persona = emp.loc[eid]
        niveles = {c: float(r[c]) if pd.notna(r[c]) else 1.0 for c in codigos}
        ajuste = 100 * sum(peso[c] * min(niveles[c] / req[c], 1) for c in codigos)
        if eid in anterior.index:
            prev = anterior.loc[eid]
            desemp = (r["desempeno_global"] + prev["desempeno_global"]) / 2
            mejora = float(np.mean([niveles[c] - float(prev[c]) for c in codigos if pd.notna(prev[c])] or [0]))
        else:  # sin evaluación anterior: solo el último año y evolución neutra
            desemp, mejora = r["desempeno_global"], 0.0
        D = 100 * (desemp - 1) / 4
        P = 100 * (r["potencial"] - 1) / 2
        T = 100 * float(np.clip(mejora + 0.5, 0, 1))
        indice = pesos["A"] * ajuste + pesos["D"] * D + pesos["P"] * P + pesos["T"] * T

        brechas = [
            {"codigo": c, "competencia": nombre[c], "actual": int(niveles[c]), "requerido": int(req[c]),
             "gap": int(req[c] - niveles[c]), "peso": round(peso[c], 3),
             "prioridad": round((req[c] - niveles[c]) * peso[c], 3)}
            for c in codigos if niveles[c] < req[c]
        ]
        brechas.sort(key=lambda b: -b["prioridad"])
        todas_brechas[eid], todos_niveles[eid] = brechas, niveles

        nivel_actual = niveles_puesto.get(persona["puesto"])
        if nivel_objetivo is not None and nivel_actual is not None and (
                nivel_actual < nivel_objetivo or (nivel_actual == nivel_objetivo and not es_nivel_base)):
            motivo = "Ya ocupa un puesto de igual o mayor nivel"
        elif r["desempeno_global"] < DESEMPENO_MINIMO:
            motivo = f"Valoración inferior a {DESEMPENO_MINIMO}"
        elif persona["interes_cambio_puesto"] != "Sí":
            motivo = "No quiere cambiar de puesto"
        else:
            motivo = ""

        avisos = []
        if area_puesto and persona["area"] != area_puesto:
            avisos.append(f"Otra área ({persona['area']})")
        faltan = jubilacion_candidatos.get(eid)
        if faltan is not None and faltan <= anios_aviso:
            avisos.append(f"Se jubila en {faltan:.0f} años".replace("en 0 años", "este año"))

        filas.append({
            "id_empleado": eid, "nombre": persona["nombre"], "puesto": persona["puesto"], "area": persona["area"],
            "anios_en_empresa": persona.get("anios_en_empresa", np.nan),
            "antiguedad_puesto_anios": persona.get("antiguedad_puesto_anios", np.nan),
            "A": redondear(ajuste), "D": redondear(D), "P": redondear(P), "T": redondear(T),
            "indice": redondear(indice), "preparacion": preparacion(ajuste, brechas),
            "n_gaps": len(brechas),
            "gaps_txt": "; ".join(f"{b['competencia']} (-{b['gap']})" for b in brechas) or "Ninguno",
            "avisos": " · ".join(avisos), "motivo_exclusion": motivo,
            "comentario": r.get("comentario_evaluador", ""),
        })

    if not filas:
        raise ValueError("No hay candidatos con evaluación de desempeño.")
    df = pd.DataFrame(filas).sort_values(["indice", "A"], ascending=False)
    elegibles = df[df["motivo_exclusion"] == ""].reset_index(drop=True)
    elegibles.insert(0, "posicion", range(1, len(elegibles) + 1))
    excluidos = df[df["motivo_exclusion"] != ""].reset_index(drop=True)
    return {"ranking": elegibles, "excluidos": excluidos, "brechas": todas_brechas,
            "niveles": todos_niveles, "pesos": pesos}
