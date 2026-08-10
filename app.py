import streamlit as st

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
