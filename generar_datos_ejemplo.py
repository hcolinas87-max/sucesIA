"""Genera los Excel de ejemplo (datos 100 % ficticios) que usa SucesIA.

Uso:  python generar_datos_ejemplo.py
Crea en la carpeta actual:
  ejemplo_plantilla.xlsx, ejemplo_organigrama.xlsx, ejemplo_diccionario_competencias.xlsx,
  ejemplo_descripcion_puestos.xlsx, ejemplo_desempeno_2024.xlsx, ejemplo_desempeno_2025.xlsx
"""
from __future__ import annotations

import random
from datetime import date

import pandas as pd

random.seed(2026)
HOY = date(2026, 10, 1)  # fecha de referencia de los datos ficticios

# ------------------------------------------------------------------ diccionario de competencias
COMPETENCIAS = [
    ("C01", "Liderazgo de equipos", "Transversal", "Dirige, motiva y desarrolla a las personas de su equipo."),
    ("C02", "Planificación y organización", "Gestión", "Ordena prioridades, recursos y plazos para cumplir objetivos."),
    ("C03", "Gestión presupuestaria", "Gestión", "Elabora, controla y defiende presupuestos y costes."),
    ("C04", "Resolución de problemas", "Transversal", "Analiza causas y aplica soluciones eficaces."),
    ("C05", "Comunicación", "Transversal", "Transmite información con claridad y escucha a los demás."),
    ("C06", "Orientación a resultados", "Transversal", "Se compromete con objetivos exigentes y los alcanza."),
    ("C07", "Seguridad y prevención (PRL)", "Técnica", "Aplica y hace cumplir las normas de seguridad y prevención."),
    ("C08", "Conocimiento técnico del área", "Técnica", "Domina los procesos, equipos y normas propios de su área."),
    ("C09", "Digitalización y datos", "Técnica", "Utiliza herramientas digitales y datos para mejorar el trabajo."),
    ("C10", "Negociación y gestión de proveedores", "Gestión", "Negocia acuerdos y gestiona la relación con proveedores y contratas."),
]
NIVELES = [
    "Básico: conoce los fundamentos y necesita supervisión.",
    "En desarrollo: lo aplica con ayuda en situaciones habituales.",
    "Competente: actúa con autonomía en situaciones habituales.",
    "Avanzado: resuelve situaciones complejas y orienta a otros.",
    "Experto: es referente, define criterios y desarrolla a otros.",
]
CODIGOS = [c[0] for c in COMPETENCIAS]

# ------------------------------------------------------------------ organigrama y descripciones de puesto
# puesto: (área, reporta_a, nivel, clave, misión, {competencia: (nivel requerido, peso)})
PUESTOS = {
    "Director/a General": ("Dirección", "", 1, "Sí", "Dirigir la empresa y su estrategia.",
                           {"C01": (5, .25), "C06": (5, .20), "C03": (5, .20), "C05": (5, .15), "C10": (4, .10), "C09": (4, .10)}),
    "Jefe/a de Producción": ("Producción", "Director/a General", 2, "Sí", "Garantizar la producción en plazo, calidad y coste.",
                             {"C01": (5, .20), "C02": (5, .20), "C06": (5, .15), "C08": (4, .15), "C07": (4, .10), "C03": (4, .10), "C09": (4, .10)}),
    "Jefe/a de Mantenimiento": ("Mantenimiento", "Director/a General", 2, "Sí", "Asegurar la disponibilidad y fiabilidad de las instalaciones.",
                                {"C01": (5, .18), "C08": (5, .18), "C03": (4, .14), "C02": (4, .12), "C07": (5, .12), "C04": (4, .10), "C10": (4, .08), "C09": (4, .08)}),
    "Responsable de Calidad": ("Calidad", "Director/a General", 2, "Sí", "Asegurar la calidad del producto y el cumplimiento de normas.",
                               {"C08": (5, .20), "C04": (5, .18), "C01": (4, .15), "C02": (4, .15), "C05": (4, .12), "C09": (4, .10), "C06": (4, .10)}),
    "Responsable de Compras": ("Compras", "Director/a General", 2, "Sí", "Conseguir materiales y servicios en coste, plazo y calidad.",
                               {"C10": (5, .25), "C03": (5, .20), "C05": (4, .15), "C06": (4, .15), "C02": (4, .15), "C09": (3, .10)}),
    "Responsable de RR. HH.": ("RR. HH.", "Director/a General", 2, "No", "Gestionar el talento y las relaciones laborales.",
                               {"C01": (4, .20), "C05": (5, .25), "C02": (4, .20), "C06": (4, .15), "C09": (3, .10), "C03": (3, .10)}),
    "Supervisor/a de turno": ("Producción", "Jefe/a de Producción", 3, "No", "Coordinar el turno de producción.",
                              {"C01": (4, .25), "C02": (4, .20), "C07": (4, .20), "C04": (4, .20), "C05": (3, .15)}),
    "Ingeniero/a de procesos": ("Producción", "Jefe/a de Producción", 3, "No", "Mejorar procesos y eficiencia de las líneas.",
                                {"C08": (4, .25), "C04": (5, .25), "C09": (4, .20), "C02": (3, .15), "C05": (3, .15)}),
    "Supervisor/a de mantenimiento": ("Mantenimiento", "Jefe/a de Mantenimiento", 3, "No", "Coordinar al equipo de técnicos de mantenimiento.",
                                      {"C01": (4, .25), "C08": (4, .25), "C07": (5, .20), "C02": (3, .15), "C04": (4, .15)}),
    "Ingeniero/a de mantenimiento": ("Mantenimiento", "Jefe/a de Mantenimiento", 3, "No", "Planificar el mantenimiento preventivo y predictivo.",
                                     {"C08": (5, .30), "C04": (4, .25), "C09": (4, .25), "C02": (4, .20)}),
    "Técnico/a de mantenimiento": ("Mantenimiento", "Supervisor/a de mantenimiento", 4, "No", "Reparar y mantener equipos e instalaciones.",
                                   {"C08": (4, .40), "C07": (4, .30), "C04": (3, .30)}),
    "Técnico/a de calidad": ("Calidad", "Responsable de Calidad", 4, "No", "Inspeccionar y controlar la calidad del producto.",
                             {"C08": (4, .35), "C04": (4, .25), "C09": (3, .20), "C05": (3, .20)}),
    "Comprador/a técnico/a": ("Compras", "Responsable de Compras", 4, "No", "Gestionar pedidos y proveedores técnicos.",
                              {"C10": (4, .40), "C03": (3, .25), "C05": (3, .20), "C09": (3, .15)}),
    "Operario/a de producción": ("Producción", "Supervisor/a de turno", 4, "No", "Operar las líneas de producción.",
                                 {"C08": (3, .40), "C07": (4, .35), "C04": (3, .25)}),
    "Técnico/a de RR. HH.": ("RR. HH.", "Responsable de RR. HH.", 4, "No", "Gestionar procesos de personas.",
                             {"C05": (4, .35), "C02": (3, .30), "C09": (3, .35)}),
    "Administrativo/a": ("Administración", "Director/a General", 4, "No", "Dar soporte administrativo.",
                         {"C02": (3, .40), "C09": (3, .35), "C05": (3, .25)}),
}

# Nivel típico en cada competencia (C01..C10) por puesto, base para generar las evaluaciones
PLANTILLA_NIVELES = {
    "Director/a General": [5, 5, 5, 4, 5, 5, 4, 4, 4, 4],
    "Jefe/a de Producción": [5, 5, 4, 4, 4, 5, 4, 4, 3, 3],
    "Jefe/a de Mantenimiento": [5, 4, 4, 5, 4, 4, 5, 5, 3, 4],
    "Responsable de Calidad": [4, 4, 3, 5, 4, 4, 4, 5, 4, 3],
    "Responsable de Compras": [4, 4, 5, 4, 4, 4, 2, 3, 3, 5],
    "Responsable de RR. HH.": [4, 4, 3, 4, 5, 4, 3, 3, 3, 3],
    "Supervisor/a de turno": [4, 4, 2, 4, 4, 4, 4, 3, 2, 2],
    "Ingeniero/a de procesos": [3, 4, 3, 5, 4, 4, 3, 4, 4, 3],
    "Supervisor/a de mantenimiento": [4, 4, 2, 4, 3, 3, 5, 4, 3, 3],
    "Ingeniero/a de mantenimiento": [3, 4, 3, 5, 3, 4, 4, 5, 4, 3],
    "Técnico/a de mantenimiento": [2, 3, 1, 4, 3, 3, 4, 4, 2, 2],
    "Técnico/a de calidad": [2, 4, 2, 4, 4, 4, 3, 4, 3, 2],
    "Comprador/a técnico/a": [2, 4, 3, 3, 4, 4, 2, 3, 3, 4],
    "Operario/a de producción": [2, 2, 1, 3, 3, 3, 3, 3, 2, 1],
    "Técnico/a de RR. HH.": [2, 3, 2, 3, 4, 3, 2, 2, 3, 2],
    "Administrativo/a": [1, 3, 2, 3, 3, 3, 2, 2, 3, 2],
}

# ------------------------------------------------------------------ personas diseñadas a mano
# id, nombre, puesto, nacimiento, incorporación, antig. puesto, interés, perf (2024, 2025), potencial,
# niveles 2024, niveles 2025 (C01..C10), comentario 2025
CLAVE = [
    ("E001", "Antonio Ruiz Gómez", "Jefe/a de Mantenimiento", "1961-03-15", "1992-02-01", 14, "No", (5, 5), 2,
     [5, 4, 4, 5, 4, 4, 5, 5, 3, 4], [5, 4, 4, 5, 4, 4, 5, 5, 3, 4],
     "Referente técnico de la planta. Conocimiento crítico no documentado."),
    ("E002", "Carmen Ortiz Vega", "Responsable de Calidad", "1960-12-02", "1995-09-01", 12, "No", (4, 4), 2,
     [4, 4, 3, 5, 4, 4, 4, 5, 3, 3], [4, 4, 3, 5, 4, 4, 4, 5, 3, 3],
     "Muy respetada por clientes y auditores."),
    ("E003", "José Luis Prieto Sanz", "Responsable de Compras", "1963-06-20", "1998-03-01", 10, "No", (4, 4), 2,
     [4, 4, 5, 4, 4, 4, 2, 3, 3, 5], [4, 4, 5, 4, 4, 4, 2, 3, 3, 5],
     "Gran negociador; relación muy personal con los proveedores clave."),
    ("E004", "Laura Martín Sanz", "Supervisor/a de mantenimiento", "1981-05-10", "2014-01-15", 6, "Sí", (4, 5), 3,
     [4, 4, 2, 4, 4, 4, 5, 4, 3, 3], [4, 4, 3, 4, 4, 4, 5, 5, 3, 3],
     "Lidera con acierto el turno de noche y redujo un 18 % las paradas no planificadas. Le falta experiencia en presupuestos y contratas."),
    ("E005", "Javier Ortega Luque", "Ingeniero/a de mantenimiento", "1988-09-03", "2020-03-01", 6, "Sí", (4, 4), 3,
     [2, 4, 3, 5, 3, 4, 4, 5, 4, 3], [3, 4, 3, 5, 3, 4, 4, 5, 5, 3],
     "Impulsó el piloto de mantenimiento predictivo con sensores. Muy técnico; aún no ha dirigido equipos."),
    ("E006", "Pedro Castillo Mora", "Supervisor/a de mantenimiento", "1974-02-18", "2002-06-01", 9, "No", (4, 4), 2,
     [4, 4, 3, 4, 4, 4, 5, 5, 3, 4], [5, 4, 3, 4, 4, 4, 5, 5, 3, 4],
     "Muy fiable. Ha dicho que no desea asumir más responsabilidad."),
    ("E007", "Daniel Vidal Romero", "Técnico/a de mantenimiento", "1976-11-25", "2005-04-01", 20, "Sí", (5, 5), 2,
     [2, 3, 1, 5, 3, 4, 5, 5, 2, 2], [2, 3, 2, 5, 3, 4, 5, 5, 3, 2],
     "El mejor diagnóstico de averías de la planta. Prefiere el trabajo técnico a la gestión."),
    ("E008", "Sofía Navarro Gil", "Técnico/a de calidad", "1990-04-12", "2016-09-01", 10, "Sí", (4, 5), 3,
     [3, 4, 2, 5, 4, 4, 3, 4, 4, 2], [3, 4, 2, 5, 4, 4, 3, 5, 4, 2],
     "Lideró la certificación ISO del último año. Muy buena comunicadora."),
    ("E009", "Marta Iglesias Prieto", "Ingeniero/a de procesos", "1985-07-30", "2012-02-01", 8, "Sí", (4, 4), 3,
     [3, 4, 3, 5, 4, 4, 3, 4, 4, 3], [4, 4, 3, 5, 4, 4, 3, 4, 5, 3],
     "Mejoró el OEE de la línea 2. Interesada en calidad."),
    ("E010", "Rubén Delgado Cano", "Comprador/a técnico/a", "1987-01-22", "2015-05-01", 7, "Sí", (4, 4), 3,
     [2, 4, 4, 3, 4, 4, 2, 3, 3, 4], [3, 4, 4, 3, 4, 5, 2, 3, 4, 5],
     "Cerró la renegociación del contrato de transporte con un 9 % de ahorro."),
]
# Otras jubilaciones próximas en puestos no clave: id, nombre, puesto, nacimiento
MAYORES = [
    ("E011", "Manuel Serrano Gil", "Técnico/a de mantenimiento", "1962-08-09"),
    ("E012", "Francisco Molina Ruiz", "Operario/a de producción", "1961-12-01"),
    ("E013", "Rosa Blanco Díaz", "Administrativo/a", "1963-02-14"),
]
# Resto de la plantilla por puesto (sin contar los anteriores)
RESTO = {
    "Director/a General": 1, "Jefe/a de Producción": 1, "Responsable de RR. HH.": 1, "Supervisor/a de turno": 4,
    "Ingeniero/a de procesos": 2, "Supervisor/a de mantenimiento": 0, "Ingeniero/a de mantenimiento": 1,
    "Técnico/a de mantenimiento": 7, "Técnico/a de calidad": 4, "Comprador/a técnico/a": 2,
    "Operario/a de producción": 20, "Técnico/a de RR. HH.": 2, "Administrativo/a": 2,
}
NOMBRES = ["Ana", "Luis", "Elena", "Miguel", "Lucía", "Raúl", "Paula", "Sergio", "Irene", "Alberto", "Nuria",
           "Óscar", "Beatriz", "Iván", "Rocío", "Hugo", "Clara", "Eva", "Mario", "Silvia", "Adrián", "Teresa",
           "Pablo", "Alicia", "Diego", "Inés", "Víctor", "Andrea", "Jorge", "Marina", "Carlos", "Lorena",
           "Álvaro", "Cristina", "Fernando", "Patricia", "Gonzalo", "Sara"]
APELLIDOS = ["García", "López", "Pérez", "Sánchez", "Romero", "Torres", "Díaz", "Moreno", "Muñoz", "Álvarez",
             "Jiménez", "Hernández", "Gil", "Castro", "Ortiz", "Rubio", "Marín", "Suárez", "Ramos", "Méndez",
             "Vega", "Flores", "Navarro", "Cabrera", "Fuentes", "León"]

FRASES_FUERTE = {
    "C01": "Sabe dirigir y motivar a su equipo.", "C02": "Muy bien organizado/a.", "C03": "Controla bien los costes.",
    "C04": "Resuelve los problemas con rapidez.", "C05": "Se comunica con claridad.", "C06": "Muy orientado/a a resultados.",
    "C07": "Ejemplar en seguridad.", "C08": "Gran dominio técnico.", "C09": "Aprovecha bien las herramientas digitales.",
    "C10": "Negocia con eficacia.",
}
FRASES_MEJORA = {
    "C01": "Debe ganar experiencia dirigiendo personas.", "C02": "Necesita planificar mejor su trabajo.",
    "C03": "Le falta experiencia con presupuestos.", "C04": "Debe profundizar en el análisis de causas.",
    "C05": "Debe mejorar su comunicación con otras áreas.", "C06": "Le cuesta cerrar objetivos a tiempo.",
    "C07": "Debe reforzar la cultura de seguridad.", "C08": "Necesita reforzar su conocimiento técnico.",
    "C09": "Debe avanzar en el uso de herramientas digitales.", "C10": "Le falta experiencia negociando.",
}


def edad(nac: str) -> int:
    n = date.fromisoformat(nac)
    return HOY.year - n.year - ((HOY.month, HOY.day) < (n.month, n.day))


def anios_desde(f: str) -> int:
    return edad(f)


def fecha_aleatoria(desde: int, hasta: int) -> str:
    return date(random.randint(desde, hasta), random.randint(1, 12), random.randint(1, 28)).isoformat()


def clip(v: int) -> int:
    return max(1, min(5, v))


def comentario(niveles: list[int]) -> str:
    pares = sorted(zip(CODIGOS, niveles), key=lambda x: x[1])
    return f"{FRASES_FUERTE[pares[-1][0]]} {FRASES_MEJORA[pares[0][0]]}"


def main() -> None:
    usados = {c[1] for c in CLAVE} | {m[1] for m in MAYORES}
    filas_emp, ev24, ev25 = [], [], []

    def alta(eid, nombre, puesto, nac, inc, antig, interes):
        area = PUESTOS[puesto][0]
        filas_emp.append({
            "id_empleado": eid, "nombre": nombre, "fecha_nacimiento": nac, "edad": edad(nac),
            "fecha_incorporacion": inc, "anios_en_empresa": anios_desde(inc),
            "antiguedad_puesto_anios": antig, "puesto": puesto, "area": area, "interes_cambio_puesto": interes,
        })

    def evaluar(eid, perf, pot, n24, n25, com):
        for lista, anio, p, n, c in ((ev24, 2024, perf[0], n24, ""), (ev25, 2025, perf[1], n25, com)):
            lista.append({"id_empleado": eid, "anio": anio, "desempeno_global": p, "potencial": pot,
                          **dict(zip(CODIGOS, n)), "comentario_evaluador": c or comentario(n)})

    for (eid, nombre, puesto, nac, inc, antig, interes, perf, pot, n24, n25, com) in CLAVE:
        alta(eid, nombre, puesto, nac, inc, antig, interes)
        evaluar(eid, perf, pot, n24, n25, com)

    for eid, nombre, puesto, nac in MAYORES:
        inc = fecha_aleatoria(1985, 1995)
        alta(eid, nombre, puesto, nac, inc, random.randint(10, 25), "No")
        base = PLANTILLA_NIVELES[puesto]
        n25 = [clip(b + random.choice([0, 0, 1])) for b in base]
        evaluar(eid, (4, 4), 1, n25, n25, "")

    n = 14
    for puesto, cuantos in RESTO.items():
        for _ in range(cuantos):
            while True:
                nombre = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
                if nombre not in usados:
                    usados.add(nombre)
                    break
            nivel = PUESTOS[puesto][2]
            joven, mayor = (1966, 1975) if nivel <= 2 else (1970, 2000)
            nac = fecha_aleatoria(joven, mayor)
            inc = fecha_aleatoria(max(int(nac[:4]) + 20, 1990), 2024)
            antig = min(random.randint(1, 12), anios_desde(inc) if anios_desde(inc) > 0 else 1)
            interes = random.choice(["Sí", "Sí", "Sí", "No"])
            eid = f"E{n:03d}"
            n += 1
            alta(eid, nombre, puesto, nac, inc, antig, interes)
            base = PLANTILLA_NIVELES[puesto]
            n25 = [clip(b + random.choice([-1, 0, 0, 0, 1])) for b in base]
            n24 = [clip(v - random.choice([0, 0, 0, 1])) for v in n25]
            p25 = random.choice([2, 3, 3, 3, 4, 4])
            p24 = clip(p25 + random.choice([-1, 0, 0, 1]))
            evaluar(eid, (p24, p25), random.choice([1, 2, 2, 3]), n24, n25, "")

    plantilla = pd.DataFrame(filas_emp).sort_values("id_empleado")
    organigrama = pd.DataFrame([
        {"puesto": p, "area": v[0], "reporta_a": v[1], "nivel_jerarquico": v[2], "puesto_clave": v[3]}
        for p, v in PUESTOS.items()
    ])
    diccionario = pd.DataFrame([
        {"codigo": c, "competencia": nmb, "tipo": t, "definicion": d, **{f"nivel_{i + 1}": NIVELES[i] for i in range(5)}}
        for c, nmb, t, d in COMPETENCIAS
    ])
    nombre_comp = {c[0]: c[1] for c in COMPETENCIAS}
    descripciones = pd.DataFrame([
        {"puesto": p, "mision": v[4], "codigo": c, "competencia": nombre_comp[c], "nivel_requerido": nr, "peso": w}
        for p, v in PUESTOS.items() for c, (nr, w) in v[5].items()
    ])

    plantilla.to_excel("ejemplo_plantilla.xlsx", index=False, sheet_name="Plantilla")
    organigrama.to_excel("ejemplo_organigrama.xlsx", index=False, sheet_name="Organigrama")
    diccionario.to_excel("ejemplo_diccionario_competencias.xlsx", index=False, sheet_name="Diccionario")
    descripciones.to_excel("ejemplo_descripcion_puestos.xlsx", index=False, sheet_name="Descripciones")
    pd.DataFrame(ev24).sort_values("id_empleado").to_excel("ejemplo_desempeno_2024.xlsx", index=False, sheet_name="Desempeno_2024")
    pd.DataFrame(ev25).sort_values("id_empleado").to_excel("ejemplo_desempeno_2025.xlsx", index=False, sheet_name="Desempeno_2025")
    print(f"{len(plantilla)} personas · {len(organigrama)} puestos · {len(descripciones)} filas de descripciones")


if __name__ == "__main__":
    main()
