import streamlit as st


@st.cache_resource
def _aquecer_kaleido():
    """Pré-carrega o Chromium do kaleido (1ª chamada baixa o executável)."""
    try:
        import plotly.graph_objects as go

        go.Figure().to_image(format="png", width=1, height=1)
    except Exception:
        pass


_aquecer_kaleido()

PAGES = [
    st.Page("paginas/0_home.py", title="Início", icon="🏠", default=True),
    st.Page("paginas/1_frota.py", title="Visão Geral da Frota", icon="🚜"),
    st.Page("paginas/2_revisoes.py", title="Revisões Preventivas", icon="🛠️"),
    st.Page("paginas/3_custos.py", title="Custos de Peças e Serviços", icon="💰"),
    st.Page("paginas/4_abastecimento.py", title="Abastecimento — Financeiro e Quantitativo", icon="⛽"),
    st.Page("paginas/5_kpis.py", title="KPIs de Abastecimento", icon="📊"),
]

nav = st.navigation(PAGES)
nav.run()
