"""Visão Geral da Frota: composição da frota com filtros e detalhamento.

Leitura dos EQUIPAMENTOS, filtros laterais (locador, equipe, situação e classe
operacional), KPIs, gráfico por tipo de equipamento e exportação em PDF.
"""
import streamlit as st

from queries import frota
from relatorio import montar_tabela
from ui_helpers import bar, base_carregada, converter_datas, dataframe_estilizado, fmt_int, kpi_cols, opcoes, plot_click, prompt_sem_base, quadro_equipamentos, set_filtro, set_page, sidebar_acoes

# Configura a página (título, ícone) e exige login.
set_page("Visão Geral da Frota", "🚜")

st.title("Visão Geral da Frota")

if not base_carregada():
    prompt_sem_base()

# DataFrame completo da frota (cache de 1h).
df = frota()

# Filtros na barra lateral; cada um vira uma seleção com a opção "Todos".
with st.sidebar:
    st.header("Filtros")
    fornecedor = st.selectbox("Fornecedor (Locador)", opcoes(df["locador"]), key="filtro_frota_locador")
    equipe = st.selectbox("Equipe", opcoes(df["equipe"]), key="filtro_frota_equipe")
    situacao = st.selectbox("Situação", opcoes(df["situacao"]), key="filtro_frota_situacao")
    classe = st.selectbox("Classe operacional", opcoes(df["classe_operacional"]), key="filtro_frota_classe")

# Aplica os filtros selecionados (cópia para não afetar o df original).
f = df.copy()
if fornecedor != "Todos":
    f = f[f["locador"] == fornecedor]
if equipe != "Todos":
    f = f[f["equipe"] == equipe]
if situacao != "Todos":
    f = f[f["situacao"] == situacao]
if classe != "Todos":
    f = f[f["classe_operacional"] == classe]

# Recortes usados nos KPIs e no gráfico.
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
# Contagem de equipamentos por classe operacional (o "tipo").
tipos = (
    f.groupby("classe_operacional")
    .size()
    .rename("quantidade")
    .reset_index()
    .sort_values("quantidade", ascending=False)
)
# Card de contagem por tipo + barra clicável (clique filtra pela classe).
quadro_equipamentos(tipos, col_tipo="classe_operacional", col_qtd="quantidade", ao_filtrar=set_filtro("filtro_frota_classe"))
fig_tipos = bar(tipos, x="classe_operacional", y="quantidade", title="Quantidade por tipo de equipamento", horizontal=True, custom_data=["classe_operacional"])
plot_click(fig_tipos, "chart_frota_tipos", set_filtro("filtro_frota_classe"))
figs = [("Quantidade por tipo de equipamento", fig_tipos)]

# Tabela detalhada (aba) — colunas escolhidas na ordem de leitura.
with st.expander("📋 Detalhamento", expanded=False):
    cols = ["prefixo", "classe_operacional", "situacao", "status", "equipe", "locador", "marca", "modelo", "ano", "placa", "data_mobilizacao"]
    visiveis = [c for c in cols if c in f.columns]
    tabela = f[visiveis].sort_values(["classe_operacional", "prefixo"])
    dataframe_estilizado(converter_datas(tabela, ["data_mobilizacao"]))
    st.caption(f"{len(f)} registros exibidos.")

# Ações da barra lateral: limpar filtros e exportar o relatório em PDF.

sidebar_acoes(
    "Visão Geral da Frota",
    figs,
    montar_tabela(
        tabela,
        visiveis,
        {
            "prefixo": ("Prefixo", "str"),
            "classe_operacional": ("Classe operacional", "str"),
            "situacao": ("Situação", "str"),
            "status": ("Status", "str"),
            "equipe": ("Equipe", "str"),
            "locador": ("Locador", "str"),
            "marca": ("Marca", "str"),
            "modelo": ("Modelo", "str"),
            "ano": ("Ano", "int"),
            "placa": ("Placa", "str"),
            "data_mobilizacao": ("Data mobilização", "date"),
        },
    ),
    periodo=f"{len(f)} equipamentos no filtro",
    nome_arquivo="relatorio_frota.pdf",
    chave="frota",
    chaves_filtro=["filtro_frota_locador", "filtro_frota_equipe", "filtro_frota_situacao", "filtro_frota_classe"],
)
