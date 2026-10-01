"""SucesIA · Herramienta de IA para el relevo generacional (máster en People Analytics).

Ejecutar en local:  streamlit run app.py
"""
from __future__ import annotations

import io
import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

import llm
from datos import (DATOS_DESEMPENO, DATOS_EMPRESA, ESQUEMAS, ErrorDatos, ejemplo, jubilaciones, leer,
                   preparar_descripciones, preparar_diccionario, preparar_organigrama, preparar_plantilla,
                   unir_desempeno)
from graficos import calendario, jubilaciones_por_anio, radar, ranking_apilado
from matching import NOMBRES_COMPONENTES, PESOS_POR_DEFECTO, calcular_ranking
from plan_formacion import TIPOS_702010, generar_plan_reglas, reparto_702010

RUTA_AUDITORIA = Path(__file__).parent / "auditoria_decisiones.csv"
AVISO_IA = "⚠️ Recomendación generada con IA, sujeta a revisión humana. La decisión corresponde al comité de talento."
HOY = date.today()

st.set_page_config(page_title="SucesIA · Relevo generacional", page_icon="🧭", layout="wide")


# ------------------------------------------------------------------ utilidades
@st.cache_data(show_spinner=False)
def leer_archivo(contenido: bytes | None, tipo: str) -> pd.DataFrame:
    return ejemplo(tipo) if contenido is None else leer(io.BytesIO(contenido), tipo)


def es(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def a_excel(hojas: dict[str, pd.DataFrame]) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for nombre, df in hojas.items():
            df.to_excel(writer, sheet_name=nombre[:31], index=False)
    return buffer.getvalue()


@st.cache_data(show_spinner="La IA está redactando las explicaciones…")
def justificaciones_ia(payload: str) -> dict[str, str]:
    return llm.justificar_ranking(json.loads(payload))


# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    st.title("🧭 SucesIA")
    st.caption("Relevo generacional con IA · People Analytics")

    origen = st.radio("Datos", ["Datos de ejemplo", "Mis archivos"], horizontal=True,
                      help="Los datos de ejemplo son ficticios y sirven para probar la herramienta.")
    archivos: dict[str, bytes | None] = {t: None for t in ESQUEMAS}
    if origen == "Mis archivos":
        with st.expander("1 · Datos de la empresa", expanded=True):
            for t in DATOS_EMPRESA:
                f = st.file_uploader(ESQUEMAS[t]["titulo"], type=["xlsx"], key=f"up_{t}")
                archivos[t] = f.getvalue() if f else b""
        with st.expander("2 · Desempeño (dos últimos años)", expanded=True):
            for t in DATOS_DESEMPENO:
                f = st.file_uploader(ESQUEMAS[t]["titulo"], type=["xlsx"], key=f"up_{t}")
                archivos[t] = f.getvalue() if f else b""

    st.subheader("Parámetros")
    edad_jub = st.number_input("Edad de jubilación", 60, 72, 67, 1)
    horizonte = st.slider("Años vista", 1, 10, 5, help="Muestra las jubilaciones de los próximos N años.")

    st.subheader("Pesos de la puntuación")
    pesos = {k: st.slider(NOMBRES_COMPONENTES[k], 0.0, 1.0, v, 0.05, key=f"peso_{k}")
             for k, v in PESOS_POR_DEFECTO.items()}
    if sum(pesos.values()) == 0:
        pesos = dict(PESOS_POR_DEFECTO)
    st.caption("Los pesos se reescalan para sumar 100 %. La edad nunca puntúa.")

    st.subheader("IA generativa")
    if llm.disponible():
        cfg = llm.configuracion()
        st.success(f"Conectada: {cfg['proveedor']} · {cfg['modelo']}")
    else:
        st.info("Sin clave de API: las explicaciones y el plan se generan con reglas. "
                "Añade LLM_PROVIDER, LLM_API_KEY y LLM_MODEL en Secrets para activar la IA.")

st.title("Relevo generacional con IA")
st.caption(AVISO_IA)

# ------------------------------------------------------------------ carga de los datos de la empresa
faltan = [ESQUEMAS[t]["titulo"] for t in DATOS_EMPRESA if archivos[t] == b""]
if faltan:
    st.info("Para empezar, sube en la barra lateral los datos de la empresa: **" + "**, **".join(faltan) + "**.")
    st.stop()
try:
    plantilla = preparar_plantilla(leer_archivo(archivos["plantilla"] or None, "plantilla"), HOY)
    organigrama = preparar_organigrama(leer_archivo(archivos["organigrama"] or None, "organigrama"))
    diccionario = preparar_diccionario(leer_archivo(archivos["diccionario"] or None, "diccionario"))
    descripciones = preparar_descripciones(leer_archivo(archivos["descripciones"] or None, "descripciones"), diccionario)
except ErrorDatos as exc:
    st.error(str(exc))
    st.stop()

jub = jubilaciones(plantilla, organigrama, edad_jub, horizonte, HOY)
todas = jubilaciones(plantilla, organigrama, edad_jub, 100, HOY)
anios_jub = dict(zip(todas["id_empleado"], todas["anios_hasta_jubilacion"]))

tab1, tab2, tab3, tab4, tab5 = st.tabs(["1 · Jubilaciones previstas", "2 · Puesto a cubrir",
                                        "3 · Candidatos recomendados", "4 · Ficha y gaps", "5 · Plan de formación"])

# ------------------------------------------------------------------ 1. Jubilaciones previstas
with tab1:
    st.subheader(f"Jubilaciones de los próximos {horizonte} años (a los {edad_jub} años)")
    if jub.empty:
        st.success("Nadie alcanza la edad de jubilación en el periodo elegido.")
        st.stop()
    c1, c2, c3 = st.columns(3)
    c1.metric("Personas que se jubilan", len(jub), f"{len(jub) / len(plantilla):.0%} de la plantilla", delta_color="off")
    c2.metric("En puestos clave", int((jub["puesto_clave"] == "Sí").sum()))
    c3.metric("Próxima jubilación", f"{jub['fecha_jubilacion'].min():%m/%Y}")
    izq, der = st.columns([2, 3])
    with izq:
        st.plotly_chart(jubilaciones_por_anio(jub), use_container_width=True)
    with der:
        st.dataframe(
            jub[["nombre", "edad", "puesto", "area", "puesto_clave", "anios_en_empresa", "fecha_jubilacion",
                 "anios_hasta_jubilacion"]],
            hide_index=True, use_container_width=True,
            column_config={
                "puesto_clave": "Puesto clave", "anios_en_empresa": "Años en la empresa",
                "fecha_jubilacion": st.column_config.DateColumn("Jubilación", format="DD/MM/YYYY"),
                "anios_hasta_jubilacion": st.column_config.NumberColumn("Años que faltan", format="%.1f"),
            })
    etiqueta = {r["id_empleado"]: f"{'⭐ ' if r['puesto_clave'] == 'Sí' else ''}{r['puesto']} · {r['nombre']} "
                f"({r['fecha_jubilacion']:%m/%Y})" for _, r in jub.iterrows()}
    id_saliente = st.selectbox("¿Qué relevo quieres preparar?", list(etiqueta), format_func=etiqueta.get)
    saliente = jub.set_index("id_empleado").loc[id_saliente]
    fecha_salida = saliente["fecha_jubilacion"]
    st.info(f"Relevo de **{saliente['puesto']}** ({saliente['nombre']}) · jubilación prevista el "
            f"**{fecha_salida:%d/%m/%Y}**. Sigue en la pestaña *2 · Puesto a cubrir*.")

# ------------------------------------------------------------------ 2. Puesto a cubrir
puesto = saliente["puesto"]
perfil_base = descripciones[descripciones["puesto"] == puesto].reset_index(drop=True)
org_puesto = organigrama[organigrama["puesto"] == puesto]
area_puesto = org_puesto["area"].iloc[0] if not org_puesto.empty else saliente["area"]
superior = org_puesto["reporta_a"].iloc[0] if not org_puesto.empty and org_puesto["reporta_a"].iloc[0] else "Dirección"

with tab2:
    st.subheader(puesto)
    if perfil_base.empty:
        st.error(f"No hay descripción para el puesto «{puesto}» en el Excel de descripciones de puestos.")
        st.stop()
    mision = perfil_base["mision"].dropna().astype(str)
    if not mision.empty and mision.iloc[0].strip():
        st.markdown(f"**Misión:** {mision.iloc[0]}")
    dependientes = organigrama[organigrama["reporta_a"] == puesto]["puesto"].tolist()
    st.caption(f"Área: {area_puesto} · Reporta a: {superior} · "
               f"Le reportan: {', '.join(dependientes) if dependientes else 'nadie'}")
    st.markdown("**Competencias que exige el puesto** (puedes ajustar el nivel y el peso)")
    perfil = st.data_editor(
        perfil_base[["codigo", "competencia", "nivel_requerido", "peso"]], hide_index=True,
        use_container_width=True, key=f"perfil_{puesto}", disabled=["codigo", "competencia"],
        column_config={
            "nivel_requerido": st.column_config.NumberColumn("Nivel requerido", min_value=1, max_value=5, step=1),
            "peso": st.column_config.NumberColumn("Peso", min_value=0.0, max_value=1.0, step=0.01, format="%.2f"),
        })
    st.caption(f"Suma de pesos: {perfil['peso'].sum():.2f} (se reescalan a 100 %).")
    dic = diccionario.set_index("codigo")
    significado = perfil.assign(
        definicion=perfil["codigo"].map(dic["definicion"]),
        que_significa=[dic.loc[c, f"nivel_{int(n)}"] if c in dic.index else "" for c, n in
                       zip(perfil["codigo"], perfil["nivel_requerido"].fillna(1).clip(1, 5))])
    with st.expander("Qué significa cada competencia y el nivel exigido (diccionario)"):
        st.dataframe(significado[["competencia", "definicion", "nivel_requerido", "que_significa"]],
                     hide_index=True, use_container_width=True)

# ------------------------------------------------------------------ desempeño
faltan_des = [ESQUEMAS[t]["titulo"] for t in DATOS_DESEMPENO if archivos[t] == b""]
res = None
if not faltan_des:
    try:
        anterior, ultimo = unir_desempeno(leer_archivo(archivos["desempeno_anterior"] or None, "desempeno_anterior"),
                                          leer_archivo(archivos["desempeno_ultimo"] or None, "desempeno_ultimo"),
                                          diccionario["codigo"].tolist())
        perfil_calc = perfil.merge(perfil_base[["codigo"]], on="codigo")
        niveles_puesto = dict(zip(organigrama["puesto"], organigrama["nivel_jerarquico"]))
        res = calcular_ranking(plantilla, anterior, ultimo, perfil_calc, id_saliente, pesos, anios_jub,
                               area_puesto, horizonte, niveles_puesto, niveles_puesto.get(puesto))
    except (ErrorDatos, ValueError) as exc:
        st.error(str(exc))
        st.stop()


def sin_desempeno():
    st.info("Sube en la barra lateral los dos Excel de desempeño: **" + "**, **".join(faltan_des) + "**.")


# ------------------------------------------------------------------ 3. Candidatos recomendados
with tab3:
    if res is None:
        sin_desempeno()
    elif res["ranking"].empty:
        st.warning("Ningún candidato cumple los criterios (nivel inferior al puesto, valoración ≥ 3 e interés en cambiar de puesto).")
    else:
        st.caption(AVISO_IA)
        ranking, excluidos = res["ranking"], res["excluidos"]
        top5 = ranking.head(5)
        c1, c2, c3 = st.columns(3)
        c1.metric("Candidatos valorados", f"{len(ranking)} de {len(ranking) + len(excluidos)}")
        c2.metric("Mejor candidato", top5.iloc[0]["nombre"], f"Índice {es(top5.iloc[0]['indice'])}", delta_color="off")
        c3.metric("Listos ahora", int((top5["preparacion"] == "Listo ahora").sum()))
        st.plotly_chart(ranking_apilado(ranking, res["pesos"]), use_container_width=True)

        justif = {r["id_empleado"]: llm.justificacion_reglas(r, res["brechas"][r["id_empleado"]])
                  for _, r in top5.iterrows()}
        origen_txt = "reglas"
        if llm.disponible():
            if st.button("✨ Explicar el ranking con IA"):
                st.session_state["pedir_ia"] = True
            if st.session_state.get("pedir_ia"):
                payload = [{"id_empleado": r["id_empleado"], "indice": r["indice"], "ajuste": r["A"],
                            "desempeno": r["D"], "potencial": r["P"], "evolucion": r["T"],
                            "preparacion": r["preparacion"], "gaps": res["brechas"][r["id_empleado"]][:4],
                            "comentario": r["comentario"]} for _, r in top5.iterrows()]  # sin nombres
                try:
                    justif.update(justificaciones_ia(json.dumps(payload, ensure_ascii=False)))
                    origen_txt = "IA"
                except Exception as exc:
                    st.warning(f"No se pudo usar la IA ({exc}). Se muestran las explicaciones por reglas.")

        st.subheader("Las 5 personas recomendadas")
        for _, r in top5.iterrows():
            with st.container(border=True):
                a, b = st.columns([3, 1])
                a.markdown(f"**{r['posicion']}. {r['nombre']}** · {r['puesto']} ({r['area']})")
                b.markdown(f"**{es(r['indice'])}** · {r['preparacion']}")
                st.write(justif.get(r["id_empleado"], ""))
                if r["avisos"]:
                    st.caption(f"ℹ️ {r['avisos']}")
                st.caption(f"Ajuste {es(r['A'])} · Desempeño {es(r['D'])} · Potencial {es(r['P'])} · "
                           f"Evolución {es(r['T'])} · Texto: {origen_txt}")
        with st.expander(f"Personas apartadas ({len(excluidos)})"):
            st.caption("Se muestran por si conviene hablar con ellas: alguien bien preparado que no quiere cambiar "
                       "de puesto es una oportunidad para una conversación de carrera.")
            st.dataframe(excluidos[["nombre", "puesto", "indice", "preparacion", "motivo_exclusion"]],
                         hide_index=True, use_container_width=True)
        with st.expander("Ranking completo"):
            st.dataframe(ranking.drop(columns=["comentario"]), hide_index=True, use_container_width=True)

# ------------------------------------------------------------------ 4. Ficha y gaps
with tab4:
    if res is None:
        sin_desempeno()
    elif not res["ranking"].empty:
        top5 = res["ranking"].head(5)
        nombres = dict(zip(top5["id_empleado"], top5["nombre"]))
        if st.session_state.get("candidato") not in nombres:
            st.session_state["candidato"] = top5["id_empleado"].iloc[0]
        id_cand = st.selectbox("Candidato", list(nombres), key="candidato", format_func=lambda i: nombres[i])
        fila = top5.set_index("id_empleado").loc[id_cand]
        gaps = res["brechas"][id_cand]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Posición", int(fila["posicion"]))
        c2.metric("Índice", es(fila["indice"]))
        c3.metric("Ajuste al puesto", f"{es(fila['A'])} %")
        c4.metric("Preparación", fila["preparacion"])
        izq, der = st.columns([3, 2])
        with izq:
            st.plotly_chart(radar(perfil, res["niveles"][id_cand], nombres[id_cand]), use_container_width=True)
        with der:
            st.markdown("**Gaps frente al puesto** (primero los que más pesan)")
            if gaps:
                g = pd.DataFrame(gaps)
                g["nivel que debe alcanzar"] = [diccionario.set_index("codigo").loc[c, f"nivel_{n}"]
                                                for c, n in zip(g["codigo"], g["requerido"])]
                st.dataframe(g[["competencia", "actual", "requerido", "gap", "nivel que debe alcanzar"]],
                             hide_index=True, use_container_width=True)
            else:
                st.success("Cumple todos los niveles requeridos.")
            st.markdown(f"**Trayectoria:** {es(fila['anios_en_empresa'])} años en la empresa · "
                        f"{fila['antiguedad_puesto_anios']} en el puesto actual")
            st.markdown("**Comentario del evaluador (último año)**")
            st.write(fila["comentario"] or "_Sin comentarios._")
            if fila["avisos"]:
                st.caption(f"ℹ️ {fila['avisos']}")

# ------------------------------------------------------------------ 5. Plan de formación
with tab5:
    if res is None:
        sin_desempeno()
    elif not res["ranking"].empty:
        st.caption(AVISO_IA)
        top5 = res["ranking"].head(5).set_index("id_empleado")
        id_cand = st.session_state.get("candidato", top5.index[0])
        if id_cand not in top5.index:
            id_cand = top5.index[0]
        fila = top5.loc[id_cand]
        st.subheader(f"Plan de formación de {fila['nombre']}")
        st.caption(f"Relevo de {puesto} · jubilación prevista el {fecha_salida:%d/%m/%Y} · "
                   "Modelo 70-20-10. Cambia de candidato en la pestaña 4.")
        with st.expander("¿Qué es el modelo 70-20-10?"):
            for k, v in TIPOS_702010.items():
                st.markdown(f"- **{k} % · {v}**")
        clave = f"plan_{id_saliente}_{id_cand}"
        usar_ia = st.toggle("Generar con IA", value=llm.disponible(), disabled=not llm.disponible())
        if st.button("Generar plan de formación", type="primary"):
            gaps = res["brechas"][id_cand]
            plan, origen_plan = None, "reglas"
            if usar_ia:
                with st.spinner("La IA está diseñando el plan…"):
                    try:
                        plan = llm.generar_plan(id_cand, puesto, fila["preparacion"], gaps, fila["comentario"],
                                                fecha_salida.date().isoformat())
                        origen_plan = "IA"
                    except Exception as exc:
                        st.warning(f"No se pudo usar la IA ({exc}). Se genera el plan con reglas.")
            if plan is None:
                plan = generar_plan_reglas(id_cand, gaps, fecha_salida, puesto, superior)
            st.session_state[clave] = {"plan": plan, "origen": origen_plan}

        guardado = st.session_state.get(clave)
        if not guardado:
            st.info("Pulsa **Generar plan de formación** para crear la propuesta.")
        else:
            plan, origen_plan = guardado["plan"], guardado["origen"]
            st.markdown(f"**Objetivo:** {plan['objetivo']}  \n_Origen del plan: {origen_plan}_")
            acc = pd.DataFrame(plan["acciones"])
            for col, defecto in (("tipo", ""), ("nueva", False), ("horas", 0.0)):
                if col not in acc.columns:
                    acc[col] = defecto
            acc["competencias"] = acc["competencias"].apply(lambda c: ", ".join(c) if isinstance(c, list) else str(c))
            acc["inicio"] = pd.to_datetime(acc["inicio"]).dt.date
            acc["fin"] = pd.to_datetime(acc["fin"]).dt.date
            acc["modelo_70_20_10"] = acc["modelo_70_20_10"].astype(str)
            editado = st.data_editor(
                acc[["modelo_70_20_10", "tipo", "accion", "competencias", "inicio", "fin", "horas", "responsable", "indicador"]],
                num_rows="dynamic", hide_index=True, use_container_width=True, key=f"editor_{clave}",
                column_config={
                    "modelo_70_20_10": st.column_config.SelectboxColumn("70-20-10", options=["70", "20", "10"]),
                    "accion": st.column_config.TextColumn("Acción", width="large"),
                    "inicio": st.column_config.DateColumn("Inicio", format="DD/MM/YYYY"),
                    "fin": st.column_config.DateColumn("Fin", format="DD/MM/YYYY"),
                    "horas": st.column_config.NumberColumn("Horas", min_value=0, step=1, format="%d"),
                })
            validas = editado.dropna(subset=["inicio", "fin", "accion"])
            if not validas.empty:
                reparto = reparto_702010(validas.to_dict("records"))
                st.markdown("**Reparto de la dedicación** (objetivo 70-20-10)")
                c1, c2, c3 = st.columns(3)
                for col, k in zip((c1, c2, c3), ["70", "20", "10"]):
                    col.metric(f"{TIPOS_702010[k].split(' (')[0]} (objetivo {k} %)", f"{reparto[k]:.0%} de las horas")
                st.plotly_chart(calendario(validas, fecha_salida, f"Jubilación de {saliente['nombre']}"),
                                use_container_width=True)
            a, b = st.columns(2)
            with a:
                st.markdown("**Revisiones de seguimiento**")
                st.write(", ".join(pd.to_datetime(h).strftime("%d/%m/%Y") for h in plan.get("hitos_revision", [])) or "—")
            with b:
                st.markdown("**Riesgos**")
                for r in plan.get("riesgos", []):
                    st.write(f"- {r}")

            nombre_archivo = f"Plan_formacion_{id_cand}_{HOY:%Y%m%d}"
            st.download_button("⬇️ Descargar plan (Excel)", a_excel({
                "Plan": editado,
                "Resumen": pd.DataFrame({
                    "campo": ["candidato", "puesto a cubrir", "jubilación", "objetivo", "origen"],
                    "valor": [fila["nombre"], puesto, f"{fecha_salida:%d/%m/%Y}", plan["objetivo"], origen_plan]}),
                "Gaps": pd.DataFrame(res["brechas"][id_cand]),
            }), f"{nombre_archivo}.xlsx")

            st.divider()
            st.subheader("Decisión del comité de talento")
            decision = st.radio("Decisión", ["Acepta", "Modifica", "Descarta"], horizontal=True)
            comentario = st.text_input("Comentario (opcional)")
            if st.button("Registrar decisión"):
                pd.DataFrame([{
                    "fecha_hora": datetime.now().isoformat(timespec="seconds"), "puesto": puesto,
                    "id_saliente": id_saliente, "id_candidato": id_cand, "posicion": int(fila["posicion"]),
                    "indice": float(fila["indice"]), "origen_plan": origen_plan, "decision": decision,
                    "comentario": comentario, "pesos": json.dumps({k: round(v, 3) for k, v in res["pesos"].items()}),
                }]).to_csv(RUTA_AUDITORIA, mode="a", header=not RUTA_AUDITORIA.exists(), index=False)
                st.success("Decisión registrada.")
            if RUTA_AUDITORIA.exists():
                st.download_button("⬇️ Descargar registro de decisiones", RUTA_AUDITORIA.read_bytes(),
                                   "auditoria_decisiones.csv", "text/csv")
