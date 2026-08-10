import pandas as pd
import streamlit as st

import data_loader as dl
from queries import diesel, frota
from ui_helpers import bar, dataframe_estilizado, fmt_br, fmt_brl, fmt_int, kpi_cols, opcoes, set_page, show_logo, theme_fig
import plotly.express as px

set_page("Abastecimento — Financeiro e Quantitativo", "⛽")

show_logo()
st.title("Abastecimento — Financeiro e Quantitativo (Diesel)")

df = diesel().copy()
df = df[df["valor"].notna() & df["quantidade"].notna()]
df["data_hora"] = pd.to_datetime(df["data_hora"])
df = df[df["data_hora"].notna()]
df["empresa_norm"] = df["empresa"].map(dl.norm_empresa)
df["ano"] = df["data_hora"].dt.year
df["mes"] = df["data_hora"].dt.month
df["periodo"] = df["data_hora"].dt.to_period("M").astype(str)

# tipo de equipamento via frota
map_classe = frota().set_index("prefixo")["classe_operacional"].to_dict()
df["tipo_equipamento"] = df["prefixo"].map(map_classe).fillna("Não identificado")

anos = sorted(df["ano"].dropna().unique().tolist())
meses = sorted(df["mes"].dropna().unique().tolist())

with st.sidebar:
    st.header("Filtros")
    ano = st.selectbox("Ano", ["Todos"] + [str(a) for a in anos])
    mes = st.selectbox("Mês", ["Todos"] + [f"{m:02d}" for m in meses])
    ponto = st.selectbox("Ponto de abastecimento", opcoes(df["ponto"]))
    empresa = st.selectbox("Empresa", opcoes(df["empresa_norm"]))
    prefixo = st.selectbox("Prefixo", opcoes(df["prefixo"]))
    equipamento = st.selectbox("Descrição do equipamento", opcoes(df["equipamento"]))

f = df
if ano != "Todos":
    f = f[f["ano"] == int(ano)]
if mes != "Todos":
    f = f[f["mes"] == int(mes)]
if ponto != "Todos":
    f = f[f["ponto"] == ponto]
if empresa != "Todos":
    f = f[f["empresa_norm"] == empresa]
if prefixo != "Todos":
    f = f[f["prefixo"] == prefixo]
if equipamento != "Todos":
    f = f[f["equipamento"] == equipamento]

periodo_ini = f["data_hora"].dropna().min()
periodo_fim = f["data_hora"].dropna().max()
if pd.notna(periodo_ini) and pd.notna(periodo_fim):
    st.caption(f"Período: {periodo_ini:%d/%m/%Y} a {periodo_fim:%d/%m/%Y}")

kpi_cols(
    [
        ("Abastecimentos (registros)", fmt_int(len(f)), "Quantidade de lançamentos"),
        ("Total abastecido", fmt_br(f["quantidade"].sum(), 0) + " L", "Soma de litros"),
        ("Valor total", fmt_brl(float(f["valor"].sum())), "Soma dos valores"),
    ]
)

col1, col2 = st.columns(2)
with col1:
    mensal = f.groupby("periodo")["quantidade"].sum().reset_index().rename(columns={"periodo": "Período", "quantidade": "Litros"})
    fig = px.bar(mensal, x="Período", y="Litros", title="Evolução do volume por mês")
    st.plotly_chart(theme_fig(fig), width="stretch")

with col2:
    por_empresa = f.groupby("empresa_norm")["valor"].sum().sort_values(ascending=False).head(12).reset_index()
    st.plotly_chart(bar(por_empresa, x="empresa_norm", y="valor", title="Valor total por empresa (top 12)", horizontal=True), width="stretch")

por_tipo = f.groupby("tipo_equipamento")["valor"].sum().sort_values(ascending=False).head(12).reset_index()
st.plotly_chart(bar(por_tipo, x="tipo_equipamento", y="valor", title="Valor total por tipo de equipamento (top 12)", horizontal=True), width="stretch")

st.markdown("### Detalhamento")
cols = ["data_hora", "empresa_norm", "prefixo", "equipamento", "tipo_equipamento", "ponto", "quantidade", "valor", "consumo"]
visiveis = [c for c in cols if c in f.columns]
tabela = f[visiveis].sort_values("data_hora", ascending=False)
dataframe_estilizado(
    tabela,
    {
        "data_hora": st.column_config.DatetimeColumn("Data/Hora", format="DD/MM/YYYY HH:mm"),
        "quantidade": st.column_config.NumberColumn("Litros", format="%.1f"),
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
    },
)
st.caption(f"{len(tabela)} registros exibidos.")
