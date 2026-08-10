from datetime import datetime
from pathlib import Path

import streamlit as st

from queries import diesel, etanol, frota, gastos, veiculos_leves
from ui_helpers import LOGO_PATH, css_logo, fmt_br, fmt_brl, fmt_int, show_logo, sidebar_importar_base

st.set_page_config(page_title="Portal de Dashboards", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")
if LOGO_PATH.exists():
    st.logo(str(LOGO_PATH), size="large")
css_logo()

DASHES = [
    (
        "🚜",
        "Visão Geral da Frota",
        "Frota de equipamentos ativos, situação, locadores e equipes por tipo de equipamento.",
        "paginas/1_frota.py",
    ),
    (
        "🛠️",
        "Revisões Preventivas",
        "Gastos com manutenção preventiva por frota e fornecedor (horímetros serão incluídos na validação).",
        "paginas/2_revisoes.py",
    ),
    (
        "💰",
        "Custos de Peças e Serviços",
        "Custos por agente causador, fornecedor, tipo de custo e detalhamento de notas fiscais.",
        "paginas/3_custos.py",
    ),
    (
        "⛽",
        "Abastecimento — Financeiro e Quantitativo",
        "Volume e valor de diesel por empresa, ponto, tipo de equipamento e evolução mensal.",
        "paginas/4_abastecimento.py",
    ),
    (
        "📊",
        "KPIs de Abastecimento",
        "Preço médio, gasto por equipe/veículo, consumo médio e postos dos veículos leves.",
        "paginas/5_kpis.py",
    ),
]

with st.sidebar:
    sidebar_importar_base()

show_logo(width=200)
st.title("Portal de Dashboards — Neovia")

base_file = Path(__file__).parent / "dados" / "base.xlsx"
fonte = st.session_state.get("_base_fonte")
if fonte:
    st.caption("Base de dados: **arquivo importado na sessão** — atualizado imediatamente.")
elif base_file.exists():
    mtime = datetime.fromtimestamp(base_file.stat().st_mtime)
    st.caption(f"Base de dados: `{base_file.name}` · atualizada em {mtime:%d/%m/%Y %H:%M}")

st.markdown("---")

df_frota = frota()
df_gastos = gastos()
df_diesel = diesel()
df_etanol = etanol()

ativos = int((df_frota["situacao"] == "ATIVO").sum())
equip_frota = df_frota["prefixo"].nunique()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Equipamentos na base", fmt_int(equip_frota))
c2.metric("Equipamentos ativos", fmt_int(ativos))
c3.metric("Total de gastos (NF)", fmt_brl(float(df_gastos["valor"].sum())))
c4.metric("Litros abastecidos (diesel)", fmt_int(df_diesel["quantidade"].sum()))

st.markdown("---")
st.subheader("Acessar dashboards")

for icon, title, desc, path in DASHES:
    with st.container(border=True):
        col_icon, col_txt = st.columns([0.5, 6])
        col_icon.markdown(f"<h1 style='margin:0'>{icon}</h1>", unsafe_allow_html=True)
        col_txt.markdown(f"**{title}**\n\n{desc}")
        col_txt.page_link(path, label="Abrir dashboard →")

st.markdown("---")
st.caption(
    "Projeto em validação — os dados são lidos diretamente da planilha base (pasta `dados/`). "
    "Extrações e indicadores serão ajustados conforme a validação do método de coleta."
)
