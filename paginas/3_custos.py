import pandas as pd
import streamlit as st

from queries import gastos
from ui_helpers import bar, dataframe_estilizado, fmt_brl, fmt_int, kpi_cols, opcoes, set_page, show_logo, theme_fig
import plotly.express as px

set_page("Custos de Peças e Serviços", "💰")

show_logo()
st.title("Custos de Peças e Serviços")

df = gastos().copy()
df = df[df["valor"].notna()]
df["empresa"] = df["locadora"].fillna("Não informado")
df["agente_causador"] = df["classe_manut"].fillna("Não classificado").str.upper()

data_min = df["data_nf"].dropna().min().date()
data_max = df["data_nf"].dropna().max().date()

with st.sidebar:
    st.header("Filtros")
    ini, fim = st.date_input("Período (Data NF)", value=(data_min, data_max), min_value=data_min, max_value=data_max)
    empresa = st.selectbox("Empresa", opcoes(df["empresa"]))
    tipo = st.selectbox("Tipo de custo (Grupo Aplicação)", opcoes(df["grupo_aplicacao"]))
    fornecedor = st.selectbox("Fornecedor", opcoes(df["fornecedor"]))
    agente = st.selectbox("Agente causador", opcoes(df["agente_causador"]))

f = df[(df["data_nf"].dt.date >= ini) & (df["data_nf"].dt.date <= fim)]
if empresa != "Todos":
    f = f[f["empresa"] == empresa]
if tipo != "Todos":
    f = f[f["grupo_aplicacao"] == tipo]
if fornecedor != "Todos":
    f = f[f["fornecedor"] == fornecedor]
if agente != "Todos":
    f = f[f["agente_causador"] == agente]

total = float(f["valor"].sum())

kpi_cols(
    [
        ("Valor total", fmt_brl(total), "Soma dos valores das notas"),
        ("Nº de notas fiscais", fmt_int(f["numero_nf"].nunique()), "Notas distintas"),
        ("Fornecedores", fmt_int(f["fornecedor"].nunique()), "Fornecedores distintos"),
        ("Lançamentos", fmt_int(len(f)), "Linhas consideradas"),
    ]
)

col1, col2 = st.columns(2)
with col1:
    agentes_df = f.groupby("agente_causador")["valor"].sum().sort_values(ascending=False).reset_index()
    agentes_df["participacao"] = agentes_df["valor"] / total * 100 if total else 0
    agentes_df["Rótulo"] = agentes_df["agente_causador"] + " (" + agentes_df["participacao"].round(1).astype(str) + "%)"
    fig = px.bar(agentes_df, x="valor", y="Rótulo", orientation="h", title="Valor total por agente causador")
    st.plotly_chart(theme_fig(fig), width="stretch")

with col2:
    fornecedores_df = f.groupby("fornecedor")["valor"].sum().sort_values(ascending=False).head(12).reset_index()
    st.plotly_chart(bar(fornecedores_df, x="fornecedor", y="valor", title="Top fornecedores", horizontal=True), width="stretch")

st.markdown("### Detalhamento")
cols = ["data_nf", "aplicacao", "fornecedor", "grupo_aplicacao", "agente_causador", "obs", "numero_nf", "valor"]
visiveis = [c for c in cols if c in f.columns]
tabela = f[visiveis].sort_values("data_nf", ascending=False)
dataframe_estilizado(
    tabela,
    {
        "data_nf": st.column_config.DatetimeColumn("Data NF", format="DD/MM/YYYY"),
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
    },
)
st.caption(f"{len(tabela)} registros exibidos. Campos *Obra* e *Link NF* ainda não existem na base.")
