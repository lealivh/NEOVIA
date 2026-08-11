"""Ponto de entrada do portal de dashboards (Main file: app.py).

Este módulo configura a navegação entre as páginas e aquece o motor de
renderização de gráficos do PDF (kaleido) na inicialização.
"""
import streamlit as st


@st.cache_resource
def _aquecer_kaleido():
    """Pré-carrega o Chromium do kaleido para os gráficos do PDF.

    O kaleido v1+ precisa de um Chrome instalado (procura em `BROWSER_PATH`
    ou no PATH). No Streamlit Cloud não há navegador, então se a renderização
    inicial falhar, baixa um Chrome for Testing via `kaleido.get_chrome_sync()`
    e aponta `BROWSER_PATH` para ele. Sem isso, os gráficos somem do PDF.
    """
    try:
        import os

        import plotly.graph_objects as go

        # Gera um PNG de 1x1: suficiente para disparar a renderização.
        go.Figure().to_image(format="png", width=1, height=1)
    except Exception:
        # Sem Chrome no ambiente: baixa um e tenta de novo (ex.: Cloud).
        try:
            import os

            import kaleido

            caminho = kaleido.get_chrome_sync(verbose=False)
            if caminho:
                os.environ["BROWSER_PATH"] = str(caminho)
            import plotly.graph_objects as go

            go.Figure().to_image(format="png", width=1, height=1)
        except Exception:
            # Se ainda falhar, o PDF tenta renderizar depois (com retry).
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
