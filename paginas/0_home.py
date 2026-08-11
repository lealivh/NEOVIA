"""Home do portal: cartões de acesso aos dashboards e resumo geral da base.

É a primeira página listada pelo `st.navigation` do `app.py`. Mostra alguns
KPIs agregados (equipamentos, ativos, gastos e litros) e links para cada
dashboard. Como o arquivo não começa com número, o Streamlit a ordena como
primeira página (prefixo `0_`).
"""
from datetime import datetime
from pathlib import Path

import streamlit as st

from queries import diesel, etanol, frota, gastos, veiculos_leves
from ui_helpers import LOGO_PATH, base_carregada, css_logo, fmt_br, fmt_brl, fmt_int, prompt_sem_base, sidebar_importar_base

# Configuração da página precisa ser o primeiro comando do Streamlit.
st.set_page_config(page_title="Portal de Dashboards", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")
if LOGO_PATH.exists():
    st.logo(str(LOGO_PATH), size="large")
css_logo()

# Aproxima o conteúdo do topo da página: reduz o preenchimento superior do
# bloco principal e a margem do título (sem o logotipo, o título sobe).
st.markdown(
    "<style>"
    '[data-testid="stMainBlockContainer"]{padding-top:1.2rem;}'
    "h1{margin-top:0 !important;}"
    "</style>",
    unsafe_allow_html=True,
)

from acesso import exigir_login

# Bloqueia a página para quem não está logado / não tem permissão.
exigir_login()

# Cards da home: (ícone, título, descrição, caminho do arquivo da página).
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

st.title("Portal de Dashboards — Neovia")

# Indica a origem da base em uso (importada na sessão ou arquivo padrão).
base_file = Path(__file__).parent / "dados" / "base.xlsx"
fonte = st.session_state.get("_base_fonte")
if fonte:
    st.caption("Base de dados: **arquivo importado na sessão** — atualizado imediatamente.")
elif base_file.exists():
    mtime = datetime.fromtimestamp(base_file.stat().st_mtime)
    st.caption(f"Base de dados: `{base_file.name}` · atualizada em {mtime:%d/%m/%Y %H:%M}")

# Sem base válida, orienta o usuário antes de seguir (upload desabilitado aqui).
if not base_carregada():
    prompt_sem_base(mostrar_upload=False)

st.markdown("---")

# Pré-carrega as tabelas (com cache) para alimentar os KPIs do resumo.
df_frota = frota()
df_gastos = gastos()
df_diesel = diesel()
df_etanol = etanol()

# KPIs globais do portal.
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
