"""Ponto de entrada do portal de dashboards (Main file: app.py).

Este módulo configura a navegação entre as páginas e aquece o motor de
renderização de gráficos do PDF (kaleido) na inicialização.
"""
import streamlit as st


@st.cache_resource
def _aquecer_kaleido():
    """Pré-carrega o Chromium do kaleido.

    O kaleido usa um navegador embutido para converter gráficos do Plotly em
    PNG. Na primeira chamada ele baixa esse executável, o que pode demorar e
    até falhar dentro do Streamlit. Aquecer na inicialização evita que a
    primeira geração de PDF (a mais demorada) aconteça na hora do clique.
    """
    try:
        import plotly.graph_objects as go

        # Gera um PNG de 1x1: suficiente para disparar o download do Chromium.
        go.Figure().to_image(format="png", width=1, height=1)
    except Exception:
        # Se falhar aqui, o PDF ainda tenta renderizar depois (com retry).
        pass


_aquecer_kaleido()

# Lista de páginas do multipage nativo do Streamlit (st.navigation).
# A primeira página marcada com default=True é a inicial ("Início").
PAGES = [
    st.Page("paginas/0_home.py", title="Início", icon="🏠", default=True),
    st.Page("paginas/1_frota.py", title="Visão Geral da Frota", icon="🚜"),
    st.Page("paginas/2_revisoes.py", title="Revisões Preventivas", icon="🛠️"),
    st.Page("paginas/3_custos.py", title="Custos de Peças e Serviços", icon="💰"),
    st.Page("paginas/4_abastecimento.py", title="Abastecimento — Financeiro e Quantitativo", icon="⛽"),
    st.Page("paginas/5_kpis.py", title="KPIs de Abastecimento", icon="📊"),
]

# Instancia a navegação e executa a página atual.
nav = st.navigation(PAGES)
nav.run()
