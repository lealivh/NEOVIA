import pandas as pd
import streamlit as st

from queries import gastos
from ui_helpers import bar, dataframe_estilizado, fmt_brl, fmt_int, kpi_cols, linha, opcoes, set_page, show_logo

set_page("Revisões Preventivas", "🛠️")

show_logo()
st.title("Revisões Preventivas")

st.info(
    "Os dados de horímetro / plano de manutenção ainda não constam na planilha base. "
    "Este painel é alimentado pelos gastos classificados como **PREVENTIVA** em GASTOS e será evoluído "
    "quando a base passar a incluir horímetro do último/próximo plano e horas restantes."
)

df = gastos()
prev = df[df["classe_manut"].str.upper().str.strip() == "PREVENTIVA"].copy()

if prev.empty:
    st.warning("Nenhum lançamento classificado como PREVENTIVA encontrado na base.")
    st.stop()

prev["mes"] = prev["data_nf"].dt.to_period("M").astype(str)
prev["empresa"] = prev["locadora"].fillna("Não informado")

with st.sidebar:
    st.header("Filtros")
    fornecedor = st.selectbox("Fornecedor", opcoes(prev["fornecedor"]))
    aplicacao = st.selectbox("Frota/Aplicação", opcoes(prev["aplicacao"]))
    meses = ["Todos"] + sorted(prev["mes"].dropna().unique().tolist(), reverse=True)
    mes = st.selectbox("Competência", meses)

f = prev
if fornecedor != "Todos":
    f = f[f["fornecedor"] == fornecedor]
if aplicacao != "Todos":
    f = f[f["aplicacao"] == aplicacao]
if mes != "Todos":
    f = f[f["mes"] == mes]

kpi_cols(
    [
        ("Revisões preventivas", fmt_int(len(f)), "Lançamentos classificados como PREVENTIVA"),
        ("Valor total", fmt_brl(float(f["valor"].sum())), "Soma dos valores das notas"),
        ("Frotas/equipamentos", fmt_int(f["aplicacao"].nunique()), "Aplicações distintas"),
        ("Fornecedores", fmt_int(f["fornecedor"].nunique()), "Fornecedores distintos"),
    ]
)

col1, col2 = st.columns(2)
with col1:
    por_frota = (
        f.groupby("aplicacao")["valor"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
        .reset_index()
        .rename(columns={"aplicacao": "Frota/Aplicação", "valor": "Valor"})
    )
    st.plotly_chart(bar(por_frota, x="Frota/Aplicação", y="Valor", title="Valor por frota/aplicação (top 15)", horizontal=True), width="stretch")

with col2:
    mensal = f.groupby("mes")["valor"].sum().reset_index().rename(columns={"mes": "Mês", "valor": "Valor"})
    st.plotly_chart(linha(mensal, x="Mês", y="Valor", title="Evolução mensal"), width="stretch")

st.markdown("### Detalhamento")
cols = ["data_nf", "numero_nf", "fornecedor", "aplicacao", "equipe", "valor", "obs"]
visiveis = [c for c in cols if c in f.columns]
tabela = f[visiveis].sort_values("data_nf", ascending=False)
dataframe_estilizado(
    tabela,
    {
        "data_nf": st.column_config.DatetimeColumn("Data NF", format="DD/MM/YYYY"),
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
    },
)
st.caption(f"{len(tabela)} registros exibidos.")
