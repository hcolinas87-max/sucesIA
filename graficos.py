"""Gráficos Plotly de SucesIA."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from matching import NOMBRES_COMPONENTES
from plan_formacion import TIPOS_702010

AZUL, GRIS = "#2a6fdb", "#9aa0a6"
COLORES_702010 = {"70": "#2a6fdb", "20": "#e8743b", "10": "#19a979"}


def jubilaciones_por_anio(jub: pd.DataFrame) -> go.Figure:
    df = jub.copy()
    df["anio"] = df["fecha_jubilacion"].dt.year.astype(str)
    df["tipo"] = df["puesto_clave"].map({"Sí": "Puesto clave", "No": "Otros puestos"})
    cuenta = df.groupby(["anio", "tipo"]).size().reset_index(name="personas")
    fig = px.bar(cuenta, x="anio", y="personas", color="tipo", text="personas",
                 color_discrete_map={"Puesto clave": AZUL, "Otros puestos": GRIS},
                 category_orders={"tipo": ["Puesto clave", "Otros puestos"]})
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Año de jubilación",
                      yaxis_title="Personas", legend_title="", plot_bgcolor="rgba(0,0,0,0)", bargap=0.4)
    fig.update_yaxes(dtick=1)
    return fig


def ranking_apilado(ranking: pd.DataFrame, pesos: dict[str, float], n: int = 5) -> go.Figure:
    top = ranking.head(n).iloc[::-1]
    opacidad = {"A": 1.0, "D": 0.65, "P": 0.42, "T": 0.22}
    fig = go.Figure()
    for k in ["A", "D", "P", "T"]:
        colores = [AZUL if i == len(top) - 1 else GRIS for i in range(len(top))]
        fig.add_bar(y=top["nombre"], x=top[k] * pesos[k], orientation="h",
                    name=f"{NOMBRES_COMPONENTES[k]} ({pesos[k]:.0%})", customdata=top[k],
                    marker=dict(color=colores, opacity=opacidad[k], line=dict(color="white", width=1)),
                    hovertemplate="%{y}<br>" + NOMBRES_COMPONENTES[k] + ": %{customdata:.1f} → aporta %{x:.1f}<extra></extra>")
    fig.add_scatter(y=top["nombre"], x=top["indice"], mode="text", showlegend=False, hoverinfo="skip",
                    text=[f"{v:.1f}".replace(".", ",") for v in top["indice"]], textposition="middle right")
    fig.update_layout(barmode="stack", height=90 + 50 * len(top), margin=dict(l=10, r=40, t=10, b=10),
                      xaxis=dict(range=[0, 108], title="Índice de idoneidad (0-100)", showgrid=False),
                      legend=dict(orientation="h", y=1.15, x=0), plot_bgcolor="rgba(0,0,0,0)")
    return fig


def radar(perfil: pd.DataFrame, niveles: dict[str, float], nombre: str) -> go.Figure:
    etiquetas = perfil["competencia"].tolist()
    req = perfil["nivel_requerido"].astype(float).tolist()
    act = [niveles[c] for c in perfil["codigo"]]
    fig = go.Figure()
    fig.add_scatterpolar(r=req + req[:1], theta=etiquetas + etiquetas[:1], name="Requerido por el puesto",
                         line=dict(color=GRIS, dash="dash"))
    fig.add_scatterpolar(r=act + act[:1], theta=etiquetas + etiquetas[:1], name=nombre, fill="toself",
                         line=dict(color=AZUL), opacity=0.8)
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 5], dtick=1)), height=440,
                      margin=dict(l=70, r=70, t=30, b=30), legend=dict(orientation="h"))
    return fig


def calendario(acciones: pd.DataFrame, fecha_salida, etiqueta_salida: str = "Jubilación") -> go.Figure:
    df = acciones.copy()
    df["inicio"] = pd.to_datetime(df["inicio"])
    df["fin"] = pd.to_datetime(df["fin"])
    df["modelo_70_20_10"] = df["modelo_70_20_10"].astype(str)
    df = df.sort_values(["inicio", "modelo_70_20_10"], kind="stable")
    df["tipo_702010"] = df["modelo_70_20_10"].map(lambda m: f"{m} % · {TIPOS_702010.get(m, '')}")
    df["fin_visual"] = df["fin"] + pd.Timedelta(days=1)
    df["etiqueta"] = df["accion"].str.slice(0, 60)
    fig = px.timeline(
        df, x_start="inicio", x_end="fin_visual", y="etiqueta", color="tipo_702010",
        color_discrete_map={f"{k} % · {v}": COLORES_702010[k] for k, v in TIPOS_702010.items()},
        hover_data={"accion": True, "inicio": "|%d/%m/%Y", "fin": "|%d/%m/%Y", "fin_visual": False,
                    "etiqueta": False, "tipo_702010": False},
    )
    fig.update_traces(marker=dict(opacity=0.65))
    salida = pd.Timestamp(fecha_salida)
    fig.add_shape(type="line", x0=salida, x1=salida, y0=0, y1=1, yref="paper",
                  line=dict(color="black", dash="dash", width=1.5))
    fig.add_annotation(x=salida, y=1, yref="paper", yanchor="bottom", xanchor="right", showarrow=False,
                       text=f"{etiqueta_salida} · {salida:%d/%m/%Y}")
    fig.update_layout(height=140 + 28 * len(df), margin=dict(l=10, r=20, t=40, b=10), bargap=0.35,
                      xaxis=dict(type="date", tickformat="%b %Y"), plot_bgcolor="rgba(0,0,0,0)",
                      yaxis=dict(categoryorder="array", categoryarray=df["etiqueta"].tolist()[::-1], title=""),
                      legend=dict(orientation="h", y=-0.12, title=""))
    return fig
