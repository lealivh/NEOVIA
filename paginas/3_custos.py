import pandas as pd
import streamlit as st

from queries import gastos
from relatorio import montar_tabela
from ui_helpers import bar, base_carregada, colorir_barras, dataframe_estilizado, fmt_brl, fmt_int, kpi_cols, opcoes, plot_click, prompt_sem_base, rotular_barras, set_filtro, set_page, sidebar_acoes, theme_fig
import plotly.express as px

set_page("Custos de Peças e Serviços", "💰")

st.title("Custos de Peças e Serviços")

if not base_carregada():
    prompt_sem_base()

df = gastos().copy()
df = df[df["valor"].notna()]
df["empresa"] = df["locadora"].fillna("Não informado")
df["agente_causador"] = df["classe_manut"].fillna("Não classificado").str.upper()

data_min = df["data_nf"].dropna().min().date()
data_max = df["data_nf"].dropna().max().date()

with st.sidebar:
    st.header("Filtros")
    ini, fim = st.date_input("Período (Data NF)", value=(data_min, data_max), min_value=data_min, max_value=data_max)
    empresa = st.selectbox("Empresa", opcoes(df["empresa"]), key="filtro_cus_empresa")
    tipo = st.selectbox("Tipo de custo (Grupo Aplicação)", opcoes(df["grupo_aplicacao"]), key="filtro_cus_tipo")
    fornecedor = st.selectbox("Fornecedor", opcoes(df["fornecedor"]), key="filtro_cus_fornecedor")
    agente = st.selectbox("Agente causador", opcoes(df["agente_causador"]), key="filtro_cus_agente")

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
    fig_agentes = theme_fig(px.bar(agentes_df, x="valor", y="Rótulo", orientation="h", title="Valor total por agente causador", custom_data=["agente_causador"]))
    fig_agentes.update_yaxes(categoryorder="total descending")
    fig_agentes = colorir_barras(fig_agentes, len(agentes_df))
    fig_agentes = rotular_barras(fig_agentes, agentes_df["valor"])
    figs = [("Valor total por agente causador", fig_agentes)]
    plot_click(fig_agentes, "chart_cus_agente", set_filtro("filtro_cus_agente"))

with col2:
    fornecedores_df = f.groupby("fornecedor")["valor"].sum().nlargest(12).reset_index()
    fig_forn = bar(fornecedores_df, x="fornecedor", y="valor", title="Valor por fornecedor (12 itens)", horizontal=True, custom_data=["fornecedor"])
    figs.append(("Valor por fornecedor (12 itens)", fig_forn))
    plot_click(fig_forn, "chart_cus_forn", set_filtro("filtro_cus_fornecedor"))

with st.expander("📋 Detalhamento", expanded=False):
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

sidebar_acoes(
    "Custos de Peças e Serviços",
    figs,
    montar_tabela(
        tabela,
        visiveis,
        {
            "data_nf": ("Data NF", "date"),
            "aplicacao": ("Aplicação", "str"),
            "fornecedor": ("Fornecedor", "str"),
            "grupo_aplicacao": ("Grupo aplicação", "str"),
            "agente_causador": ("Agente causador", "str"),
            "obs": ("Observação", "str"),
            "numero_nf": ("Nº NF", "str"),
            "valor": ("Valor", "brl"),
        },
    ),
    periodo=f"{ini:%d/%m/%Y} a {fim:%d/%m/%Y}",
    nome_arquivo="relatorio_custos.pdf",
    chave="custos",
    chaves_filtro=["filtro_cus_empresa", "filtro_cus_tipo", "filtro_cus_fornecedor", "filtro_cus_agente"],
)
