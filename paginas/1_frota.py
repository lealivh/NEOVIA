import streamlit as st

from queries import frota
from ui_helpers import bar, dataframe_estilizado, fmt_int, kpi_cols, opcoes, set_page, show_logo

set_page("Visão Geral da Frota", "🚜")

show_logo()
st.title("Visão Geral da Frota")

df = frota()

with st.sidebar:
    st.header("Filtros")
    fornecedor = st.selectbox("Fornecedor (Locador)", opcoes(df["locador"]))
    equipe = st.selectbox("Equipe", opcoes(df["equipe"]))
    situacao = st.selectbox("Situação", opcoes(df["situacao"]))

f = df.copy()
if fornecedor != "Todos":
    f = f[f["locador"] == fornecedor]
if equipe != "Todos":
    f = f[f["equipe"] == equipe]
if situacao != "Todos":
    f = f[f["situacao"] == situacao]

ativos = f[f["situacao"] == "ATIVO"]
mobilizados = f[f["status"] == "MOBILIZADO"]
kpi_cols(
    [
        ("Equipamentos ativos na obra", fmt_int(len(ativos)), "Equipamentos com situação ATIVO"),
        ("Total de equipamentos", fmt_int(len(f)), "Todos os registros do filtro"),
        ("Mobilizados", fmt_int(len(mobilizados)), "Equipamentos com status MOBILIZADO"),
        ("Locadores distintos", fmt_int(f["locador"].nunique()), "Fornecedores/locadores na seleção"),
    ]
)

st.markdown("### Equipamentos por tipo")
tipos = (
    f.groupby("classe_operacional")
    .size()
    .rename("quantidade")
    .reset_index()
    .sort_values("quantidade", ascending=False)
)
st.plotly_chart(bar(tipos, x="classe_operacional", y="quantidade", title="Quantidade por tipo de equipamento", horizontal=True), width="stretch")

st.markdown("### Detalhamento")
cols = ["prefixo", "classe_operacional", "situacao", "status", "equipe", "locador", "marca", "modelo", "ano", "placa", "data_mobilizacao"]
visiveis = [c for c in cols if c in f.columns]
tabela = f[visiveis].sort_values(["classe_operacional", "prefixo"])
dataframe_estilizado(tabela)

st.caption(f"{len(f)} registros exibidos.")
