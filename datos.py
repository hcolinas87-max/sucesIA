"""Carga y validación de los Excel de SucesIA.

Cada archivo se lee de su primera hoja. Las columnas obligatorias están en ESQUEMAS.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

CARPETA = Path(__file__).parent

ESQUEMAS: dict[str, dict] = {
    "plantilla": {
        "titulo": "Plantilla",
        "columnas": ["id_empleado", "nombre", "fecha_incorporacion", "antiguedad_puesto_anios",
                     "puesto", "area", "interes_cambio_puesto"],
        "ejemplo": "ejemplo_plantilla.xlsx",
    },
    "organigrama": {
        "titulo": "Organigrama",
        "columnas": ["puesto", "area", "reporta_a", "nivel_jerarquico", "puesto_clave"],
        "ejemplo": "ejemplo_organigrama.xlsx",
    },
    "diccionario": {
        "titulo": "Diccionario de competencias",
        "columnas": ["codigo", "competencia", "definicion", "nivel_1", "nivel_2", "nivel_3", "nivel_4", "nivel_5"],
        "ejemplo": "ejemplo_diccionario_competencias.xlsx",
    },
    "descripciones": {
        "titulo": "Descripción de puestos",
        "columnas": ["puesto", "codigo", "nivel_requerido", "peso"],
        "ejemplo": "ejemplo_descripcion_puestos.xlsx",
    },
    "desempeno_anterior": {
        "titulo": "Desempeño año anterior",
        "columnas": ["id_empleado", "desempeno_global", "potencial"],
        "ejemplo": "ejemplo_desempeno_2024.xlsx",
    },
    "desempeno_ultimo": {
        "titulo": "Desempeño último año",
        "columnas": ["id_empleado", "desempeno_global", "potencial"],
        "ejemplo": "ejemplo_desempeno_2025.xlsx",
    },
}
DATOS_EMPRESA = ["plantilla", "organigrama", "diccionario", "descripciones"]
DATOS_DESEMPENO = ["desempeno_anterior", "desempeno_ultimo"]


class ErrorDatos(Exception):
    """Error de estructura o contenido de un Excel, con un mensaje legible."""


def _si_no(serie: pd.Series) -> pd.Series:
    s = serie.fillna("").astype(str).str.strip().str.lower()
    return s.map(lambda v: "Sí" if v in {"sí", "si", "s", "yes", "y", "1", "true", "verdadero"} else "No")


def leer(fuente, tipo: str) -> pd.DataFrame:
    """Lee un Excel (ruta o archivo subido) y comprueba sus columnas."""
    esquema = ESQUEMAS[tipo]
    try:
        df = pd.read_excel(fuente)
    except Exception as exc:
        raise ErrorDatos(f"{esquema['titulo']}: no se ha podido leer el archivo ({exc}).") from exc
    df.columns = [str(c).strip().lower() for c in df.columns]
    faltan = [c for c in esquema["columnas"] if c not in df.columns]
    if tipo == "plantilla" and "fecha_nacimiento" not in df.columns and "edad" not in df.columns:
        faltan.append("fecha_nacimiento o edad")
    if faltan:
        raise ErrorDatos(f"{esquema['titulo']}: faltan las columnas {', '.join(faltan)}.")
    if df.empty:
        raise ErrorDatos(f"{esquema['titulo']}: el archivo no tiene filas.")
    return df


def ejemplo(tipo: str) -> pd.DataFrame:
    return leer(CARPETA / ESQUEMAS[tipo]["ejemplo"], tipo)


# ------------------------------------------------------------------ preparación
def preparar_plantilla(df: pd.DataFrame, hoy: date) -> pd.DataFrame:
    df = df.copy()
    df["id_empleado"] = df["id_empleado"].astype(str).str.strip()
    if df["id_empleado"].duplicated().any():
        raise ErrorDatos("Plantilla: hay id_empleado repetidos.")
    hoy_ts = pd.Timestamp(hoy)
    if "fecha_nacimiento" in df.columns:
        df["fecha_nacimiento"] = pd.to_datetime(df["fecha_nacimiento"], errors="coerce")
    else:
        df["fecha_nacimiento"] = pd.NaT
    # Edad: se calcula con la fecha de nacimiento; si no la hay, se usa la columna edad
    calculada = ((hoy_ts - df["fecha_nacimiento"]).dt.days / 365.25).apply(lambda x: int(x) if pd.notna(x) else None)
    if "edad" in df.columns:
        df["edad"] = calculada.fillna(pd.to_numeric(df["edad"], errors="coerce"))
    else:
        df["edad"] = calculada
    if df["edad"].isna().any():
        raise ErrorDatos("Plantilla: hay personas sin fecha de nacimiento ni edad.")
    df["edad"] = df["edad"].astype(int)
    df["fecha_incorporacion"] = pd.to_datetime(df["fecha_incorporacion"], errors="coerce")
    df["anios_en_empresa"] = ((hoy_ts - df["fecha_incorporacion"]).dt.days / 365.25).round(1)
    df["interes_cambio_puesto"] = _si_no(df["interes_cambio_puesto"])
    df["puesto"] = df["puesto"].astype(str).str.strip()
    df["area"] = df["area"].astype(str).str.strip()
    return df


def preparar_organigrama(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["puesto"] = df["puesto"].astype(str).str.strip()
    df["reporta_a"] = df["reporta_a"].fillna("").astype(str).str.strip()
    df["puesto_clave"] = _si_no(df["puesto_clave"])
    df["nivel_jerarquico"] = pd.to_numeric(df["nivel_jerarquico"], errors="coerce")
    return df


def preparar_diccionario(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["codigo"] = df["codigo"].astype(str).str.strip()
    return df


def preparar_descripciones(df: pd.DataFrame, diccionario: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["puesto"] = df["puesto"].astype(str).str.strip()
    df["codigo"] = df["codigo"].astype(str).str.strip()
    desconocidas = sorted(set(df["codigo"]) - set(diccionario["codigo"]))
    if desconocidas:
        raise ErrorDatos("Descripción de puestos: estas competencias no están en el diccionario: "
                         + ", ".join(desconocidas))
    nombres = dict(zip(diccionario["codigo"], diccionario["competencia"]))
    df["competencia"] = df["codigo"].map(nombres)
    if "mision" not in df.columns:
        df["mision"] = ""
    return df


def unir_desempeno(anterior: pd.DataFrame, ultimo: pd.DataFrame, codigos: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (anterior, último) indexados por id_empleado y con las competencias del diccionario."""
    salida = []
    for nombre, df in (("Desempeño año anterior", anterior), ("Desempeño último año", ultimo)):
        df = df.copy()
        df["id_empleado"] = df["id_empleado"].astype(str).str.strip()
        faltan = [c for c in codigos if c not in [x.upper() for x in df.columns]]
        if faltan:
            raise ErrorDatos(f"{nombre}: faltan las columnas de competencias {', '.join(faltan)}.")
        df.columns = [c.upper() if c.upper() in codigos else c for c in df.columns]
        if "comentario_evaluador" not in df.columns:
            df["comentario_evaluador"] = ""
        df["comentario_evaluador"] = df["comentario_evaluador"].fillna("").astype(str)
        salida.append(df.drop_duplicates("id_empleado", keep="last").set_index("id_empleado"))
    return salida[0], salida[1]


def jubilaciones(plantilla: pd.DataFrame, organigrama: pd.DataFrame, edad_jubilacion: int,
                 horizonte: int, hoy: date) -> pd.DataFrame:
    """Personas que llegan a la edad de jubilación en los próximos `horizonte` años."""
    hoy_ts = pd.Timestamp(hoy)
    df = plantilla.copy()

    def fecha_jub(r):
        if pd.notna(r["fecha_nacimiento"]):
            return r["fecha_nacimiento"] + pd.DateOffset(years=edad_jubilacion)
        return hoy_ts + pd.DateOffset(years=max(edad_jubilacion - int(r["edad"]), 0))

    df["fecha_jubilacion"] = df.apply(fecha_jub, axis=1)
    df["anios_hasta_jubilacion"] = ((df["fecha_jubilacion"] - hoy_ts).dt.days / 365.25).round(1)
    org = organigrama[["puesto", "puesto_clave", "nivel_jerarquico"]].drop_duplicates("puesto")
    df = df.merge(org, on="puesto", how="left")
    df["puesto_clave"] = df["puesto_clave"].fillna("No")
    limite = hoy_ts + pd.DateOffset(years=horizonte)
    df = df[df["fecha_jubilacion"] <= limite]
    return df.sort_values(["puesto_clave", "fecha_jubilacion"], ascending=[False, True]).reset_index(drop=True)
