import pandas as pd
import streamlit as st
import plotly.express as px

from queries import etanol, veiculos_leves
from relatorio import montar_tabela
from ui_helpers import bar, colorir_barras, dataframe_estilizado, fmt_br, fmt_brl, fmt_int, kpi_cols, opcoes, plot_click, rotular_barras, set_filtro, set_page, sidebar_acoes, theme_fig

set_page("KPIs de Abastecimento", "📊")

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
    ano = st.selectbox("Ano", ["Todos"] + [str(a) for a in anos], key="filtro_kpi_ano")
    mes = st.selectbox("Mês", ["Todos"] + [f"{m:02d}" for m in meses], key="filtro_kpi_mes")
    placa = st.selectbox("Veículo (placa)", opcoes(df["placa"]), key="filtro_kpi_placa")
    motorista = st.selectbox("Motorista", opcoes(df["motorista"]), key="filtro_kpi_motorista")
    posto = st.selectbox("Posto", opcoes(df["estabelecimento"]), key="filtro_kpi_posto")
    equipe = st.selectbox("Equipe", opcoes(df["equipe"]), key="filtro_kpi_equipe")

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
if equipe != "Todos":
    f = f[f["equipe"] == equipe]


def _filtra_periodo(v):
    if isinstance(v, str) and "-" in v:
        ano_s, mes_s = v.split("-")[:2]
        st.session_state["filtro_kpi_ano"] = ano_s
        st.session_state["filtro_kpi_mes"] = f"{int(mes_s):02d}"

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
    fig_preco = theme_fig(px.line(preco, x="Período", y="Preço médio (R$/L)", title="Evolução do preço médio do litro", markers=True, custom_data=["Período"]))
    figs = [("Evolução do preço médio do litro", fig_preco)]
    plot_click(fig_preco, "chart_kpi_preco", _filtra_periodo)

with col2:
    por_equipe = f.groupby("equipe")["valor"].sum().nlargest(12).reset_index()
    fig_equipe = bar(por_equipe, x="equipe", y="valor", title="Gasto com combustível por equipe (12 itens)", horizontal=True, custom_data=["equipe"])
    figs.append(("Gasto com combustível por equipe (12 itens)", fig_equipe))
    plot_click(fig_equipe, "chart_kpi_equipe", set_filtro("filtro_kpi_equipe"))

col3, col4 = st.columns(2)
with col3:
    por_veiculo = f.groupby("placa")["valor"].sum().nlargest(12).reset_index()
    fig_veiculo = bar(por_veiculo, x="placa", y="valor", title="Total gasto por veículo (12 itens)", horizontal=True, custom_data=["placa"])
    figs.append(("Total gasto por veículo (12 itens)", fig_veiculo))
    plot_click(fig_veiculo, "chart_kpi_veiculo", set_filtro("filtro_kpi_placa"))

with col4:
    consumo = (
        f.assign(km_litro=pd.to_numeric(f["km_litro"], errors="coerce"))
        .loc[lambda d: d["km_litro"].notna()]
        .groupby("placa")["km_litro"]
        .mean()
        .nlargest(12)
        .reset_index()
    )
    fig_consumo = theme_fig(px.bar(consumo, x="km_litro", y="placa", orientation="h", title="Consumo médio por veículo (km/L, 12 itens)", custom_data=["placa"]))
    fig_consumo.update_yaxes(categoryorder="total descending")
    fig_consumo = colorir_barras(fig_consumo, len(consumo))
    fig_consumo = rotular_barras(fig_consumo, consumo["km_litro"])
    figs.append(("Consumo médio por veículo (km/L, 12 itens)", fig_consumo))
    plot_click(fig_consumo, "chart_kpi_consumo", set_filtro("filtro_kpi_placa"))

with st.expander("📋 Detalhamento", expanded=False):
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

sidebar_acoes(
    "KPIs de Abastecimento (Veículos Leves)",
    figs,
    montar_tabela(
        tabela,
        visiveis,
        {
            "data_transacao": ("Data", "datetime"),
            "placa": ("Placa", "str"),
            "motorista": ("Motorista", "str"),
            "equipe": ("Equipe", "str"),
            "modelo": ("Modelo", "str"),
            "estabelecimento": ("Posto", "str"),
            "litros": ("Litros", "num"),
            "preco": ("R$/L", "num"),
            "km_litro": ("Km/L", "num"),
            "valor": ("Valor", "brl"),
        },
    ),
    periodo=f"{len(f)} lançamentos",
    nome_arquivo="relatorio_kpis.pdf",
    chave="kpis",
    chaves_filtro=["filtro_kpi_ano", "filtro_kpi_mes", "filtro_kpi_placa", "filtro_kpi_motorista", "filtro_kpi_posto", "filtro_kpi_equipe"],
)
