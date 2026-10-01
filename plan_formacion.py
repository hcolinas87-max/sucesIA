"""Plan de formación 70-20-10 basado en reglas (se usa sin clave de API o si la IA falla).

70 % aprendizaje experiencial: retos reales, proyectos y resolución de problemas en el puesto.
20 % aprendizaje social: mentoría con quien se jubila, coaching, feedback y observación.
10 % aprendizaje formal: cursos, talleres, webinars, e-learning y lecturas.
"""
from __future__ import annotations

import re
from datetime import date

import pandas as pd

TIPOS_702010 = {
    "70": "Experiencial (aprender haciendo)",
    "20": "Social (aprender de los demás)",
    "10": "Formal (aprender estudiando)",
}

# Acciones por competencia: (70 experiencial, 10 curso/taller, 10 lectura)
ACCIONES = {
    "C01": ("Liderar un equipo de mejora de 4-6 personas durante un proyecto del área",
            "Curso de liderazgo de equipos (40 h)",
            "Lectura: «Las cinco disfunciones de un equipo» (P. Lencioni)"),
    "C02": ("Planificar y coordinar la parada anual o un proyecto completo del área",
            "Taller de planificación y gestión de proyectos (16 h)",
            "Lectura: «Organízate con eficacia» (D. Allen)"),
    "C03": ("Elaborar y defender ante dirección el presupuesto anual del área",
            "Curso de finanzas para mandos no financieros (20 h)",
            "Lectura: manual interno de control de costes del área"),
    "C04": ("Liderar el análisis de causa raíz de las tres incidencias más repetidas",
            "Taller de métodos de resolución de problemas (8D, Ishikawa) (12 h)",
            "Lectura: «La meta» (E. Goldratt)"),
    "C05": ("Presentar cada mes los resultados del área en el comité de dirección",
            "Taller de comunicación eficaz y presentaciones (12 h)",
            "Lectura: «Conversaciones cruciales» (K. Patterson y otros)"),
    "C06": ("Asumir un objetivo de mejora medible del área y rendir cuentas de él",
            "Webinar de gestión por objetivos e indicadores (4 h)",
            "Lectura: «Las 4 disciplinas de la ejecución» (C. McChesney y otros)"),
    "C07": ("Coordinar la próxima auditoría de seguridad y su plan de acción",
            "Curso de prevención de riesgos laborales, nivel intermedio (60 h)",
            "Lectura: guías técnicas del INSST aplicables al área"),
    "C08": ("Rotar por los procesos e instalaciones críticos del puesto con un responsable",
            "Formación técnica específica del área con proveedor o centro tecnológico (30 h)",
            "Lectura: procedimientos y documentación técnica crítica del puesto"),
    "C09": ("Liderar la implantación de una herramienta digital o un cuadro de mando del área",
            "E-learning de análisis de datos y herramientas digitales (20 h)",
            "Lectura: manual de uso del ERP / GMAO de la empresa"),
    "C10": ("Renegociar un contrato con un proveedor o una contrata del área",
            "Taller de negociación (12 h)",
            "Lectura: «Obtenga el sí» (R. Fisher y W. Ury)"),
}
TRANSVERSALES = {"C01", "C04", "C05", "C06"}
GESTION = {"C02", "C03", "C10"}


def _tramos(inicio: pd.Timestamp, fin: pd.Timestamp, n: int) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    if n == 0:
        return []
    limites = pd.date_range(inicio, fin, periods=n + 1)
    return [(limites[i], limites[i + 1] - pd.Timedelta(days=1)) for i in range(n)]


def _accion(id_, modelo, tipo, texto, comps, responsable, indicador, horas=0.0):
    return {"id_accion": id_, "modelo_70_20_10": modelo, "tipo": tipo, "accion": texto,
            "competencias": list(comps), "responsable": responsable, "indicador": indicador,
            "horas": horas, "nueva": False}


def _horas_curso(texto: str) -> float:
    m = re.search(r"\((\d+) h\)", texto)
    return float(m.group(1)) if m else 10.0


def reparto_702010(acciones) -> dict[str, float]:
    """Reparto de la dedicación (horas) entre 70, 20 y 10. Si no hay horas, cuenta acciones."""
    df = pd.DataFrame(acciones)
    if df.empty:
        return {"70": 0.0, "20": 0.0, "10": 0.0}
    df["modelo_70_20_10"] = df["modelo_70_20_10"].astype(str)
    horas = pd.to_numeric(df.get("horas", 0), errors="coerce").fillna(0)
    base = horas if horas.sum() > 0 else pd.Series(1.0, index=df.index)
    tot = base.groupby(df["modelo_70_20_10"]).sum()
    return {k: float(tot.get(k, 0) / base.sum()) for k in ["70", "20", "10"]}


def generar_plan_reglas(id_candidato: str, brechas: list[dict], fecha_salida, puesto: str,
                        responsable_area: str = "Responsable del área", hoy: date | None = None,
                        max_gaps: int = 4) -> dict:
    hoy_ts = pd.Timestamp(hoy or date.today()).normalize()
    salida = pd.Timestamp(fecha_salida).normalize()
    fin_plan = salida - pd.DateOffset(months=3)
    riesgos: list[str] = []
    if salida <= hoy_ts:
        salida = hoy_ts + pd.DateOffset(months=6)
        fin_plan = salida - pd.DateOffset(months=1)
        riesgos.append("La persona ya ha alcanzado la edad de jubilación: el plan es urgente y muy comprimido.")
    elif fin_plan <= hoy_ts + pd.Timedelta(days=90):
        fin_plan = salida
        riesgos.append("Queda poco tiempo hasta la jubilación: el plan no deja periodo de solapamiento.")

    gaps = brechas[:max_gaps]
    codigos = [b["codigo"] for b in gaps]
    exp, soc, form = [], [], []

    # 20 % social: mentoría con quien se jubila, siempre
    soc.append(_accion("S1", "20", "Mentoría", "Mentoría semanal (2 h) con la persona que se jubila para transferir el conocimiento crítico",
                       codigos or ["C08"], "Persona que se jubila",
                       "Procesos críticos documentados al 100 % antes de la jubilación"))
    for b in gaps:
        c = b["codigo"]
        texto70, curso, lectura = ACCIONES.get(c, (f"Proyecto práctico para desarrollar {b['competencia']}",
                                                     f"Formación en {b['competencia']}", f"Lectura sobre {b['competencia']}"))
        exp.append(_accion(f"E{len(exp) + 1}", "70", "Proyecto / reto", texto70, [c], responsable_area,
                           f"Entregable aprobado y nivel en {b['competencia']} ≥ {b['requerido']} en la próxima evaluación", 80))
        form.append(_accion(f"F{len(form) + 1}", "10", "Curso / taller", curso, [c], "RR. HH. (Formación)",
                            "Formación completada con evaluación ≥ 7/10", _horas_curso(curso)))
        form.append(_accion(f"F{len(form) + 1}", "10", "Lectura", lectura, [c], "Propia persona",
                            "Resumen de aplicaciones prácticas comentado con el mentor", 10))
    if set(codigos) & TRANSVERSALES:
        soc.append(_accion("S2", "20", "Coaching", "Proceso de coaching con coach interno o externo (6 sesiones)",
                           sorted(set(codigos) & TRANSVERSALES), "RR. HH. (Desarrollo)",
                           "Plan de acción del coaching cumplido y feedback 180° positivo", 9))
    if set(codigos) & GESTION:
        soc.append(_accion("S3", "20", "Observación", "Acompañar a la persona que se jubila en comités, negociaciones y reuniones de presupuesto",
                           sorted(set(codigos) & GESTION), "Persona que se jubila",
                           "Asistencia a ≥ 80 % de las reuniones clave del periodo", 40))
    soc.append(_accion(f"S{len(soc) + 1}", "20", "Feedback", "Feedback trimestral del responsable sobre el avance del plan",
                       codigos or ["C08"], responsable_area, "Cuatro revisiones de feedback documentadas al año", 8))
    exp.insert(0, _accion("E0", "70", "Sustitución", "Sustituir a la persona que se jubila en vacaciones y ausencias",
                          codigos or ["C08"], responsable_area, "Periodos de sustitución cubiertos sin incidencias críticas", 160))

    # Calendario: la formación formal al principio, la práctica a lo largo del plan
    duracion = fin_plan - hoy_ts
    for a, (i, f) in zip(form, _tramos(hoy_ts, hoy_ts + duracion * 0.5, len(form))):
        a["inicio"], a["fin"] = i, f
    for a, (i, f) in zip(exp, _tramos(hoy_ts + duracion * 0.15, fin_plan, len(exp))):
        a["inicio"], a["fin"] = i, f
    for a in soc:
        a["inicio"], a["fin"] = hoy_ts, fin_plan
    soc[0]["horas"] = float(round(max((fin_plan - hoy_ts).days / 7, 1) * 2))  # mentoría: 2 h por semana
    acciones = exp + soc + form
    if fin_plan < salida:
        acciones.append(_accion("E99", "70", "Traspaso", "Solapamiento y traspaso de funciones", [], "Persona que se jubila",
                                "Traspaso completado sin incidencias críticas", 240))
        acciones[-1]["inicio"], acciones[-1]["fin"] = fin_plan + pd.Timedelta(days=1), salida
    for a in acciones:
        a["inicio"] = pd.Timestamp(a["inicio"]).date().isoformat()
        a["fin"] = pd.Timestamp(a["fin"]).date().isoformat()

    if len(brechas) > max_gaps:
        riesgos.append(f"Tiene {len(brechas)} gaps; el plan se centra en los {max_gaps} más importantes.")
    for b in gaps:
        if b["gap"] >= 2:
            riesgos.append(f"Gap de {b['gap']} puntos en {b['competencia']}: puede no cerrarse a tiempo.")
    riesgos.append("Sobrecarga al compatibilizar el plan con el puesto actual: reservar tiempo en la agenda.")

    return {
        "objetivo": f"Preparar a {id_candidato} para asumir el puesto de {puesto} antes del "
                    f"{salida.date().isoformat()}, cerrando {len(gaps)} gap(s) prioritario(s).",
        "acciones": acciones,
        "hitos_revision": [d.date().isoformat() for d in pd.date_range(hoy_ts, fin_plan, freq="3MS")[1:]],
        "riesgos": riesgos,
    }
