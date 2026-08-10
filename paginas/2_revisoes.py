import pandas as pd
import streamlit as st

from queries import gastos
from relatorio import montar_tabela
from ui_helpers import bar, dataframe_estilizado, fmt_brl, fmt_int, kpi_cols, linha, opcoes, plot_click, set_filtro, set_page, sidebar_acoes

set_page("Revisões Preventivas", "🛠️")

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
    fornecedor = st.selectbox("Fornecedor", opcoes(prev["fornecedor"]), key="filtro_rev_fornecedor")
    aplicacao = st.selectbox("Frota/Aplicação", opcoes(prev["aplicacao"]), key="filtro_rev_aplicacao")
    meses = ["Todos"] + sorted(prev["mes"].dropna().unique().tolist(), reverse=True)
    mes = st.selectbox("Competência", meses, key="filtro_rev_mes")

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
        .nlargest(15)
        .reset_index()
        .rename(columns={"aplicacao": "Frota/Aplicação", "valor": "Valor"})
    )
    fig_frota = bar(por_frota, x="Frota/Aplicação", y="Valor", title="Valor por frota/aplicação (15 itens)", horizontal=True, custom_data=["Frota/Aplicação"])
    figs = [("Valor por frota/aplicação (15 itens)", fig_frota)]
    plot_click(fig_frota, "chart_rev_frota", set_filtro("filtro_rev_aplicacao"))

with col2:
    mensal = f.groupby("mes")["valor"].sum().reset_index().rename(columns={"mes": "Mês", "valor": "Valor"})
    fig_mensal = linha(mensal, x="Mês", y="Valor", title="Evolução mensal", custom_data=["Mês"])
    figs.append(("Evolução mensal dos gastos preventivos", fig_mensal))
    plot_click(fig_mensal, "chart_rev_mensal", set_filtro("filtro_rev_mes"))

with st.expander("📋 Detalhamento", expanded=False):
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

sidebar_acoes(
    "Revisões Preventivas",
    figs,
    montar_tabela(
        tabela,
        visiveis,
        {
            "data_nf": ("Data NF", "date"),
            "numero_nf": ("Nº NF", "str"),
            "fornecedor": ("Fornecedor", "str"),
            "aplicacao": ("Frota/Aplicação", "str"),
            "equipe": ("Equipe", "str"),
            "valor": ("Valor", "brl"),
            "obs": ("Observação", "str"),
        },
    ),
    periodo=f"{len(f)} lançamentos PREVENTIVA",
    nome_arquivo="relatorio_revisoes.pdf",
    chave="revisoes",
    chaves_filtro=["filtro_rev_fornecedor", "filtro_rev_aplicacao", "filtro_rev_mes"],
)
