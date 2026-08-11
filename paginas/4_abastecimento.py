import pandas as pd
import streamlit as st

import data_loader as dl
from queries import diesel, frota
from relatorio import montar_tabela
from ui_helpers import bar, base_carregada, colorir_barras, dataframe_estilizado, fmt_br, fmt_brl, fmt_int, kpi_cols, opcoes, plot_click, prompt_sem_base, rotular_barras, set_filtro, set_page, sidebar_acoes, theme_fig
import plotly.express as px

set_page("Abastecimento — Financeiro e Quantitativo", "⛽")

st.title("Abastecimento — Financeiro e Quantitativo (Diesel)")

if not base_carregada():
    prompt_sem_base()

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
    ano = st.selectbox("Ano", ["Todos"] + [str(a) for a in anos], key="filtro_abs_ano")
    mes = st.selectbox("Mês", ["Todos"] + [f"{m:02d}" for m in meses], key="filtro_abs_mes")
    ponto = st.selectbox("Ponto de abastecimento", opcoes(df["ponto"]), key="filtro_abs_ponto")
    empresa = st.selectbox("Empresa", opcoes(df["empresa_norm"]), key="filtro_abs_empresa")
    prefixo = st.selectbox("Prefixo", opcoes(df["prefixo"]), key="filtro_abs_prefixo")
    equipamento = st.selectbox("Descrição do equipamento", opcoes(df["equipamento"]), key="filtro_abs_equipamento")
    tipo_equip = st.selectbox("Tipo de equipamento", opcoes(df["tipo_equipamento"]), key="filtro_abs_tipo_equip")

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
if tipo_equip != "Todos":
    f = f[f["tipo_equipamento"] == tipo_equip]


def _filtra_periodo(v):
    if isinstance(v, str) and "-" in v:
        ano_s, mes_s = v.split("-")[:2]
        st.session_state["filtro_abs_ano"] = ano_s
        st.session_state["filtro_abs_mes"] = f"{int(mes_s):02d}"

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
    fig_mensal = theme_fig(px.bar(mensal, x="Período", y="Litros", title="Evolução do volume por mês", custom_data=["Período"]))
    fig_mensal = colorir_barras(fig_mensal, len(mensal))
    fig_mensal = rotular_barras(fig_mensal, mensal["Litros"])
    figs = [("Evolução do volume por mês", fig_mensal)]
    plot_click(fig_mensal, "chart_abs_mensal", _filtra_periodo)

with col2:
    por_empresa = f.groupby("empresa_norm")["valor"].sum().nlargest(12).reset_index()
    fig_empresa = bar(por_empresa, x="empresa_norm", y="valor", title="Valor total por empresa (12 itens)", horizontal=True, custom_data=["empresa_norm"])
    figs.append(("Valor total por empresa (12 itens)", fig_empresa))
    plot_click(fig_empresa, "chart_abs_empresa", set_filtro("filtro_abs_empresa"))

por_tipo = f.groupby("tipo_equipamento")["valor"].sum().nlargest(12).reset_index()
fig_tipo = bar(por_tipo, x="tipo_equipamento", y="valor", title="Valor total por tipo de equipamento (12 itens)", horizontal=True, custom_data=["tipo_equipamento"])
figs.append(("Valor total por tipo de equipamento (12 itens)", fig_tipo))
plot_click(fig_tipo, "chart_abs_tipo", set_filtro("filtro_abs_tipo_equip"))

with st.expander("📋 Detalhamento", expanded=False):
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

periodo_txt = ""
if pd.notna(periodo_ini) and pd.notna(periodo_fim):
    periodo_txt = f"{periodo_ini:%d/%m/%Y} a {periodo_fim:%d/%m/%Y}"
sidebar_acoes(
    "Abastecimento — Financeiro e Quantitativo (Diesel)",
    figs,
    montar_tabela(
        tabela,
        visiveis,
        {
            "data_hora": ("Data/Hora", "datetime"),
            "empresa_norm": ("Empresa", "str"),
            "prefixo": ("Prefixo", "str"),
            "equipamento": ("Equipamento", "str"),
            "tipo_equipamento": ("Tipo de equipamento", "str"),
            "ponto": ("Ponto", "str"),
            "quantidade": ("Litros", "num"),
            "valor": ("Valor", "brl"),
            "consumo": ("Consumo", "num"),
        },
    ),
    periodo=periodo_txt,
    nome_arquivo="relatorio_abastecimento.pdf",
    chave="abastecimento",
    chaves_filtro=[
        "filtro_abs_ano",
        "filtro_abs_mes",
        "filtro_abs_ponto",
        "filtro_abs_empresa",
        "filtro_abs_prefixo",
        "filtro_abs_equipamento",
        "filtro_abs_tipo_equip",
    ],
)
