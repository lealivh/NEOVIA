import pandas as pd
import streamlit as st
import plotly.express as px

from queries import etanol, veiculos_leves
from ui_helpers import bar, dataframe_estilizado, fmt_br, fmt_brl, fmt_int, kpi_cols, opcoes, set_page, show_logo, theme_fig

set_page("KPIs de Abastecimento", "📊")

show_logo()
st.title("KPIs de Abastecimento (Veículos Leves)")

df = etanol().copy()
df = df[df["valor"].notna() & df["litros"].notna()]
df["data_transacao"] = pd.to_datetime(df["data_transacao"])
df = df[df["data_transacao"].notna()]
df["ano"] = df["data_transacao"].dt.year
df["mes"] = df["data_transacao"].dt.month
df["periodo"] = df["data_transacao"].dt.to_period("M").astype(str)
df["preco"] = df["valor"] / df["litros"]

setor_map = veiculos_leves().dropna(subset=["placa"]).set_index("placa")["setor"].to_dict()
df["equipe"] = df["placa"].map(setor_map).fillna("Não identificada")

anos = sorted(df["ano"].dropna().unique().tolist())
meses = sorted(df["mes"].dropna().unique().tolist())

with st.sidebar:
    st.header("Filtros")
    ano = st.selectbox("Ano", ["Todos"] + [str(a) for a in anos])
    mes = st.selectbox("Mês", ["Todos"] + [f"{m:02d}" for m in meses])
    placa = st.selectbox("Veículo (placa)", opcoes(df["placa"]))
    motorista = st.selectbox("Motorista", opcoes(df["motorista"]))
    posto = st.selectbox("Posto", opcoes(df["estabelecimento"]))

f = df
if ano != "Todos":
    f = f[f["ano"] == int(ano)]
if mes != "Todos":
    f = f[f["mes"] == int(mes)]
if placa != "Todos":
    f = f[f["placa"] == placa]
if motorista != "Todos":
    f = f[f["motorista"] == motorista]
if posto != "Todos":
    f = f[f["estabelecimento"] == posto]

kpi_cols(
    [
        ("Valor total", fmt_brl(float(f["valor"].sum())), "Soma dos valores emitidos"),
        ("Postos utilizados", fmt_int(f["estabelecimento"].nunique()), "Estabelecimentos distintos"),
        ("Abastecimentos", fmt_int(len(f)), "Lançamentos no período"),
        ("Veículos abastecidos", fmt_int(f["placa"].nunique()), "Placas distintas"),
        ("Motoristas", fmt_int(f["motorista"].nunique()), "Motoristas distintos"),
    ]
)

col1, col2 = st.columns(2)
with col1:
    preco = f.groupby("periodo")["preco"].mean().reset_index().rename(columns={"periodo": "Período", "preco": "Preço médio (R$/L)"})
    fig = px.line(preco, x="Período", y="Preço médio (R$/L)", title="Evolução do preço médio do litro", markers=True)
    st.plotly_chart(theme_fig(fig), width="stretch")

with col2:
    por_equipe = f.groupby("equipe")["valor"].sum().sort_values(ascending=False).head(12).reset_index()
    st.plotly_chart(bar(por_equipe, x="equipe", y="valor", title="Gasto com combustível por equipe (top 12)", horizontal=True), width="stretch")

col3, col4 = st.columns(2)
with col3:
    por_veiculo = f.groupby("placa")["valor"].sum().sort_values(ascending=False).head(12).reset_index()
    st.plotly_chart(bar(por_veiculo, x="placa", y="valor", title="Total gasto por veículo (top 12)", horizontal=True), width="stretch")

with col4:
    consumo = (
        f[f["km_litro"].notna()]
        .groupby("placa")["km_litro"]
        .mean()
        .sort_values(ascending=False)
        .head(12)
        .reset_index()
    )
    fig = px.bar(consumo, x="km_litro", y="placa", orientation="h", title="Consumo médio por veículo (km/L, top 12)")
    st.plotly_chart(theme_fig(fig), width="stretch")

st.markdown("### Detalhamento")
cols = ["data_transacao", "placa", "motorista", "equipe", "modelo", "estabelecimento", "litros", "preco", "km_litro", "valor"]
visiveis = [c for c in cols if c in f.columns]
tabela = f[visiveis].sort_values("data_transacao", ascending=False)
dataframe_estilizado(
    tabela,
    {
        "data_transacao": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
        "litros": st.column_config.NumberColumn("Litros", format="%.1f"),
        "preco": st.column_config.NumberColumn("R$/L", format="%.2f"),
        "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
    },
)
st.caption(f"{len(tabela)} registros exibidos. A equipe é mapeada pela placa via aba VEICULOS LEVES.")
