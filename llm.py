"""Componente de IA generativa de SucesIA.

Configuración en los Secrets de Streamlit (o en .streamlit/secrets.toml en local):
    LLM_PROVIDER = "openai"      # o "anthropic"
    LLM_API_KEY  = "..."
    LLM_MODEL    = "..."         # nombre del modelo según la documentación del proveedor

Privacidad: a la IA solo se envían ids, puntuaciones, gaps y comentarios. Nunca nombres, edad ni sexo.
"""
from __future__ import annotations

import json
import os
from datetime import date

from pydantic import BaseModel, Field, ValidationError, field_validator

SISTEMA_PLAN = (
    "Eres consultor/a de desarrollo de talento en RR. HH. Diseñas planes de formación para preparar "
    "relevos generacionales con el modelo 70-20-10: "
    "70 = aprendizaje experiencial (retos reales, nuevos proyectos y resolución de problemas en el puesto); "
    "20 = aprendizaje social (mentoría con la persona que se jubila, coaching, feedback y observación de "
    "profesionales con experiencia); "
    "10 = aprendizaje formal (cursos, talleres, webinars, e-learning y lecturas). "
    "Reglas: 1) cada acción trabaja uno o varios gaps y se prioriza por gap x peso; 2) estima las horas "
    "de dedicación de cada acción y haz que el reparto de horas se parezca al 70-20-10; 3) incluye siempre una mentoría con la persona que se jubila; "
    "4) todo termina al menos 3 meses antes de FECHA_SALIDA para dejar un periodo de traspaso; "
    "5) cada acción lleva tipo, competencias, inicio, fin, responsable e indicador medible; "
    "6) acciones concretas y realistas para una empresa industrial; 7) no uses ni infieras edad, sexo ni "
    "datos personales; 8) responde solo con JSON válido según ESQUEMA."
)
SISTEMA_JUSTIFICACION = (
    "Eres analista de People Analytics. Explicas en español, de forma clara, neutral y comparable, por qué "
    "cada candidato ocupa su posición en un ranking de relevo. No uses ni infieras edad, sexo ni datos "
    "personales. Responde solo con JSON válido."
)


class Accion(BaseModel):
    id_accion: str
    modelo_70_20_10: str
    tipo: str = ""
    accion: str
    competencias: list[str] = Field(default_factory=list)
    inicio: date
    fin: date
    responsable: str
    indicador: str
    horas: float = 0
    nueva: bool = False

    @field_validator("modelo_70_20_10", "id_accion", mode="before")
    @classmethod
    def _texto(cls, v):  # la IA a veces devuelve 70 en vez de "70"
        return str(v).strip().replace("%", "")

    @field_validator("competencias", mode="before")
    @classmethod
    def _lista(cls, v):
        return [c.strip() for c in v.replace(",", ";").split(";")] if isinstance(v, str) else v


class Plan(BaseModel):
    objetivo: str
    acciones: list[Accion]
    hitos_revision: list[date] = Field(default_factory=list)
    riesgos: list[str] = Field(default_factory=list)


ESQUEMA_PLAN = {
    "objetivo": "str",
    "acciones": [{"id_accion": "str", "modelo_70_20_10": "70|20|10", "tipo": "Proyecto|Mentoría|Coaching|Curso|Lectura|...",
                  "accion": "str", "competencias": ["C01"], "inicio": "AAAA-MM-DD", "fin": "AAAA-MM-DD",
                  "responsable": "str", "indicador": "str medible", "horas": "dedicación estimada en horas", "nueva": False}],
    "hitos_revision": ["AAAA-MM-DD"],
    "riesgos": ["str"],
}


# ------------------------------------------------------------------ configuración
def _secreto(nombre: str) -> str:
    try:
        import streamlit as st
        valor = st.secrets.get(nombre, "")
    except Exception:  # sin secrets o fuera de Streamlit
        valor = ""
    return str(valor or os.environ.get(nombre, "")).strip()


def configuracion() -> dict:
    return {"proveedor": _secreto("LLM_PROVIDER").lower() or "openai",
            "clave": _secreto("LLM_API_KEY"), "modelo": _secreto("LLM_MODEL")}


def disponible() -> bool:
    cfg = configuracion()
    return bool(cfg["clave"] and cfg["modelo"] and cfg["proveedor"] in {"anthropic", "openai"})


def _llamar(sistema: str, usuario: str, max_tokens: int = 3000) -> str:
    cfg = configuracion()
    if cfg["proveedor"] == "anthropic":
        import anthropic
        cliente = anthropic.Anthropic(api_key=cfg["clave"])
        resp = cliente.messages.create(model=cfg["modelo"], max_tokens=max_tokens, temperature=0.2,
                                       system=sistema, messages=[{"role": "user", "content": usuario}])
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    from openai import OpenAI
    cliente = OpenAI(api_key=cfg["clave"])
    resp = cliente.chat.completions.create(
        model=cfg["modelo"], temperature=0.2, max_tokens=max_tokens, response_format={"type": "json_object"},
        messages=[{"role": "system", "content": sistema}, {"role": "user", "content": usuario}])
    return resp.choices[0].message.content or ""


def _json(texto: str) -> dict:
    ini, fin = texto.find("{"), texto.rfind("}")
    if ini == -1 or fin == -1:
        raise ValueError("La respuesta de la IA no contiene JSON.")
    return json.loads(texto[ini:fin + 1])


# ------------------------------------------------------------------ tareas
def generar_plan(id_candidato: str, puesto: str, preparacion: str, gaps: list[dict], comentario: str,
                 fecha_salida: str) -> dict:
    usuario = (
        f"PUESTO A CUBRIR: {puesto} | FECHA_SALIDA: {fecha_salida} | HOY: {date.today().isoformat()}\n"
        f"CANDIDATO: {id_candidato} | Preparación: {preparacion}\n"
        f"GAPS (codigo, competencia, actual, requerido, gap, peso): {json.dumps(gaps, ensure_ascii=False)}\n"
        f"COMENTARIO DEL EVALUADOR: {comentario or 'sin comentarios'}\n"
        f"ESQUEMA: {json.dumps(ESQUEMA_PLAN, ensure_ascii=False)}"
    )
    error = None
    for _ in range(2):  # un reintento si el JSON no es válido
        try:
            plan = Plan.model_validate(_json(_llamar(SISTEMA_PLAN, usuario)))
            return json.loads(plan.model_dump_json())
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            error = exc
    raise RuntimeError(f"La IA no devolvió un plan válido: {error}")


def justificar_ranking(candidatos: list[dict]) -> dict[str, str]:
    usuario = (
        "Para cada candidato, escribe 3 frases que expliquen su posición en el ranking de relevo: fortalezas, "
        'gaps principales y qué le diferencia de los demás. Formato: {"justificaciones": {"<id_empleado>": "<texto>"}}\n'
        f"CANDIDATOS: {json.dumps(candidatos, ensure_ascii=False)}"
    )
    return {str(k): str(v) for k, v in _json(_llamar(SISTEMA_JUSTIFICACION, usuario, 2000)).get("justificaciones", {}).items()}


# ------------------------------------------------------------------ texto de respaldo sin IA
def _es(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def justificacion_reglas(fila, gaps: list[dict]) -> str:
    fuertes = []
    if fila["A"] >= 85:
        fuertes.append(f"un ajuste competencial alto ({_es(fila['A'])} %)")
    if fila["D"] >= 85:
        fuertes.append("un desempeño sostenido muy alto")
    if fila["P"] >= 100:
        fuertes.append("potencial alto")
    if fila["T"] >= 85:
        fuertes.append("una clara evolución entre evaluaciones")
    texto = f"Índice {_es(fila['indice'])}. "
    texto += ("Destaca por " + ", ".join(fuertes) + ". ") if fuertes else "Perfil equilibrado, sin un rasgo dominante. "
    if gaps:
        texto += "Gaps prioritarios: " + ", ".join(f"{g['competencia']} (-{g['gap']})" for g in gaps[:3]) + ". "
    else:
        texto += "Cumple todos los niveles requeridos. "
    return texto + f"Preparación estimada: {fila['preparacion']}."
