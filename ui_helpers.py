from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_loader as dl

PROJ_DIR = Path(__file__).parent
LOGO_PATH = PROJ_DIR / "assets" / "logo.png"

COLORWAY = [
    "#1F6FB2",
    "#2E9E8F",
    "#F2B705",
    "#D9534F",
    "#7A5CF0",
    "#E07A3F",
    "#5CA858",
    "#8E6B4A",
    "#4FA3D1",
    "#C44E9C",
]


def set_page(title: str, icon: str):
    st.set_page_config(page_title=title, page_icon=icon, layout="wide", initial_sidebar_state="expanded")


def fmt_br(v: float, decimals: int = 2) -> str:
    if v is None or (isinstance(v, float) and v != v):
        return "—"
    return f"{v:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_brl(v: float) -> str:
    return "R$ " + fmt_br(v)


def fmt_int(v) -> str:
    return f"{int(v):,}".replace(",", ".")


def opcoes(series: pd.Series, rotulo: str = "Todos"):
    """Lista ordenada de opções para filtros, normalizando tipos mistos."""
    vals = [str(v) for v in series.dropna().unique().tolist()]
    return [rotulo] + sorted(vals)


def show_logo(width: int = 220):
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=width)


def kpi_cols(items: list[tuple[str, str, str]]):
    """items: lista de (rótulo, valor, ajuda)."""
    cols = st.columns(len(items))
    for col, (label, value, help_) in zip(cols, items):
        col.metric(label, value, help=help_)


def theme_fig(fig):
    fig.update_layout(
        template="plotly_white",
        colorway=COLORWAY,
        font=dict(family="Segoe UI, Arial", size=12),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def bar(df: pd.DataFrame, x: str, y: str, title: str, horizontal: bool = False, top: int | None = None):
    d = df.copy()
    if top:
        d = d.head(top)
    if horizontal:
        fig = px.bar(d, x=y, y=x, orientation="h", title=title)
    else:
        fig = px.bar(d, x=x, y=y, title=title)
    fig.update_traces(marker_color=COLORWAY[0])
    return theme_fig(fig)


def linha(df: pd.DataFrame, x: str, y: str, title: str):
    fig = px.line(df, x=x, y=y, title=title, markers=True)
    return theme_fig(fig)


def dataframe_estilizado(df: pd.DataFrame, colunas: dict | None = None):
    st.dataframe(df, column_config=colunas, use_container_width=True, hide_index=True)
