"""Componentes de interface reutilizados pelas páginas.

Concentra: estilos/marca (logo, cores), formatação pt-BR, gráficos Plotly
padronizados, quadro de equipamentos com ícones, importação da base.xlsx na
sessão, geração de PDF (barra lateral) e controles de login/permissão.
"""
import base64
import html
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_loader as dl
from acesso import exigir_login, permissao

# Caminhos fixos dentro do projeto (logo e ícones dos equipamentos).
PROJ_DIR = Path(__file__).parent
LOGO_PATH = PROJ_DIR / "assets" / "logo.png"
ICONES_DIR = PROJ_DIR / "assets" / "icons"

# Paleta da marca (cores do logotipo da Neovia) usada em gráficos e PDF.
BRAND = {
    "vermelho": "#D00B13",          # vermelho principal do logotipo
    "vermelho_escuro": "#71140F",   # vermelho escuro do degradê
    "preto": "#231F1F",             # preto do logotipo e menu
    "branco": "#FFFFFF",            # branco do cabeçalho
    "cinza_icones": "#9B9897",      # cinza dos ícones sociais
    "cinza_claro": "#CCCCCB",       # cinza-claro do título
    "cinza_medio": "#484849",       # cinza médio da fotografia
    "cinza_grafite": "#343434",     # cinza grafite
    "fundo_escuro": "#181818",      # fundo escuro da sobreposição
    "preto_profundo": "#050505",    # preto profundo da imagem
}

# Sequência de cores aplicada às barras/linhas dos gráficos.
COLORWAY = [
    BRAND["vermelho"],
    BRAND["vermelho_escuro"],
    BRAND["preto"],
    BRAND["cinza_grafite"],
    BRAND["cinza_medio"],
    BRAND["cinza_icones"],
    BRAND["cinza_claro"],
    BRAND["fundo_escuro"],
    BRAND["preto_profundo"],
]


def set_page(title: str, icon: str):
    """Configura a página (título/ícone), logo, CSS e exige login.

    É a primeira função chamada em cada página: sem ela, `exigir_login()` não
    roda e a tela ficaria acessível sem autenticação.
    """
    st.set_page_config(page_title=title, page_icon=icon, layout="wide", initial_sidebar_state="expanded")
    if LOGO_PATH.exists():
        st.logo(str(LOGO_PATH), size="large")
    css_logo()
    exigir_login()


def css_logo():
    """Aumenta a logomarca no topo da barra lateral (st.logo).

    A largura bate com a do `show_logo(200)` usado no corpo da home, para as
    duas exibições ficarem parecidas. O PNG da marca já tem o fundo
    transparente, então a imagem se mistura com o cinza da barra lateral.
    """
    st.markdown(
        '<style>[data-testid="stSidebarLogo"]{width:200px !important;height:auto !important;}</style>',
        unsafe_allow_html=True,
    )


def fmt_br(v: float, decimals: int = 2) -> str:
    """Formata número no padrão brasileiro (1.234,56). `—` para nulos/NaN."""
    if v is None or (isinstance(v, float) and v != v):
        return "—"
    # Truque: formata com separador de milhar do Python, troca vírgula/ponto.
    return f"{v:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_brl(v: float) -> str:
    """Formata valor monetário em reais (R$ 1.234,56)."""
    return "R$ " + fmt_br(v)


def fmt_int(v) -> str:
    """Formata inteiro com separador de milhar brasileiro (1.234)."""
    return f"{int(v):,}".replace(",", ".")


def opcoes(series: pd.Series, rotulo: str = "Todos"):
    """Lista ordenada de opções para filtros, normalizando tipos mistos.

    Converte tudo em string para o `selectbox`; adiciona a opção "Todos".
    """
    vals = [str(v) for v in series.dropna().unique().tolist()]
    return [rotulo] + sorted(vals)


def show_logo(width: int = 220):
    """Exibe o logotipo no corpo da página (ex.: home)."""
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=width)


def kpi_cols(items: list[tuple[str, str, str]]):
    """Linha de KPIs: cada item é (rótulo, valor, texto de ajuda)."""
    cols = st.columns(len(items))
    for col, (label, value, help_) in zip(cols, items):
        col.metric(label, value, help=help_)


def theme_fig(fig):
    """Aplica o tema padrão (fundo branco, paleta da marca) a uma figura Plotly."""
    fig.update_layout(
        template="plotly_white",
        colorway=COLORWAY,
        font=dict(family="Segoe UI, Arial", size=12),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def _rotulo_valor(v) -> str:
    """Rótulo compacto para os valores das barras (separador de milhar pt-BR)."""
    if v is None or (isinstance(v, float) and v != v):
        return ""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if f.is_integer():
        return f"{int(f):,}".replace(",", ".")
    return f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def colorir_barras(fig, n: int):
    """Aplica a paleta da marca às barras, ciclando uma cor por barra."""
    fig.update_traces(marker_color=[COLORWAY[i % len(COLORWAY)] for i in range(n)])
    return fig


def rotular_barras(fig, valores: pd.Series):
    """Adiciona rótulos de valor (pt-BR) nas barras de um gráfico plotly."""
    fig.update_traces(
        text=valores.map(_rotulo_valor),
        textposition="outside",
        cliponaxis=False,
    )
    return fig


# Mapa de tipos de equipamento → arquivo PNG do ícone (assets/icons/).
# Tipos sem PNG caem no fallback de emoji (_EMOJI_FALLBACK).
ICONES_EQUIPAMENTOS = {
    "CAM.BASCULANTE": "Caminhão Basculante.png",
    "CAM. CARROCERIA": "Caminhão Carroceria.png",
    "CAM. SINALIZAÇÃO": "Caminhão Sinalização.png",
    "CAM.PIPA": "Caminhão Pipa.png",
    "CAM.ESPARGIDOR": "Caminhão Espargidor.png",
    "CAM.LUBRIFICADOR": "Caminhão Lubrificador.png",
    "CAM.COMPRESSOR": "Caminhão Compressor.png",
    "CAV.MECÂNICO": "Cavalo Mecânico.png",
    "COMPRESSOR DE AR": "Compressor de Ar.png",
    "ESCAVADEIRA HIDRAULICA": "Escavadeira Hidráulica.png",
    "ESCAVADEIRA ESTEIRA": "Escavadeira Hidráulica.png",
    "MINI ESCAVADEIRA": "Escavadeira Hidráulica.png",
    "FRESADORA": "Fresadora.png",
    "IMPLEMENTO - FRESA": "Fresadora.png",
    "GERADOR": "Gerador.png",
    "IMPLEMENTO - VASSOURA": "Implemento Vassoura.png",
    "MINI CARREGADEIRA": "Mini Carregadeira.png",
    "PÁ CARREGADEIRA": "Pá Carregadeira.png",
    "ROLO CORRUGADO": "Rolo Corrugado.png",
    "ROLO PNEUS": "Rolo de Pneus.png",
    "ROM PNEUMATICO": "Rolo de Pneus.png",
    "ROLO TANDEM": "Rolo Tandem.png",
    "ROLO COMBINADO": "Rolo Tandem.png",
    "SEMI REBOQUE PRANCHA": "Semi Reboque Prancha.png",
    "SEMI REBOQUE TANQUE": "Semi Reboque Tanque.png",
    "CARRETA SILO": "Semi Reboque Tanque.png",
    "TANQUE FIXO": "Semi Reboque Tanque.png",
    "USINA DE ASFALTO": "Usina Asfalto.png",
    "USINA": "Usina Asfalto.png",
    "VIBRO ACABADORA DE ESTEIRA": "Vibro Acabadora.png",
    "MICROONIBUS": "Ônibus-Micro Ônibus.png",
    "ONIBUS": "Ônibus-Micro Ônibus.png",
    "VAN": "Veículo Leve.png",
    "BRITAGEM": "Britador Mandibula.png",
}

# Fallback: regex (case-insensitive) → emoji quando não há PNG do tipo.
# A ordem importa: padrões mais específicos vêm primeiro (ex.: TRATOR DE
# PNEUS antes de TRATOR genérico).
_EMOJI_FALLBACK = [
    (r"TRATOR DE PNEUS", "🚜"),
    (r"TRATOR DE ESTEIRAS?$", "🚜"),
    (r"TRATOR", "🚜"),
    (r"BOMBA", "🚛"),
    (r"BETONEIRA", "🚚"),
    (r"CONTAINER", "📦"),
    (r"PLATAFORMA", "🏗️"),
    (r"MUNCK", "🏗️"),
    (r"OFICINA", "🔧"),
    (r"POLICORTE", "🪚"),
    (r"ROMPEDOR", "⛏️"),
    (r"CARRETINHA", "🚛"),
    (r"RECICLADORA", "⚙️"),
    (r"RETROESCAVADEIRA", "🚜"),
    (r"VALETADEIRA|MOTONIVELADORA|ESTABILIZADORA", "🚜"),
    (r"DISTRIBUIDOR|CONSERVA", "🚚"),
    (r"CAM\.", "🚚"),
]
_EMOJI_PADRAO = "🚧"

# CSS do quadro de equipamentos (cards com ícone, descrição e quantidade).
_QUADRO_CSS = """
<style>
.quadro-card{border:1px solid #CCCCCB;border-radius:10px;padding:14px 8px 10px;background:#FFFFFF;
 text-align:center;margin-bottom:10px;height:100%;}
.quadro-card img{width:72px;height:72px;object-fit:contain;}
.quadro-emoji{font-size:56px;line-height:1;margin:4px 0 8px;}
.quadro-tipo{font-size:12px;font-weight:600;color:#231F1F;line-height:1.25;min-height:32px;margin:6px 0 4px;}
.quadro-qtd{font-size:24px;font-weight:800;color:#D00B13;}
</style>
"""


def _icone_equipamento(tipo: str) -> tuple[str | None, str | None]:
    """Retorna (caminho_do_png | None, emoji | None) para o tipo de equipamento.

    Prioridade: PNG específico > emoji de fallback > emoji padrão.
    """
    nome = ICONES_EQUIPAMENTOS.get(tipo)
    if nome:
        path = ICONES_DIR / nome
        if path.exists():
            return str(path), None
    for padrao, emoji in _EMOJI_FALLBACK:
        if re.search(padrao, tipo, re.IGNORECASE):
            return None, emoji
    return None, _EMOJI_PADRAO


def quadro_equipamentos(
    dados: pd.DataFrame,
    col_tipo: str = "classe_operacional",
    col_qtd: str = "quantidade",
    cols_por_linha: int = 4,
    ao_filtrar=None,
):
    """Quadro com ícone, descrição do tipo de equipamento e quantidade (ordem A→Z).

    `ao_filtrar`: callable recebendo o tipo (ex.: `set_filtro(...)`) — cria um
    botão "Filtrar" em cada card quando informado.
    """
    st.markdown(_QUADRO_CSS, unsafe_allow_html=True)
    itens = dados.sort_values(col_tipo).to_dict("records")
    if not itens:
        st.caption("Nenhum tipo de equipamento no filtro atual.")
        return
    # Organiza os cards em linhas com `cols_por_linha` colunas.
    for i in range(0, len(itens), cols_por_linha):
        cols = st.columns(cols_por_linha)
        for col, item in zip(cols, itens[i : i + cols_por_linha]):
            tipo = str(item[col_tipo])
            qtd = item[col_qtd]
            img, emoji = _icone_equipamento(tipo)
            with col:
                if img:
                    # PNG embutido em base64 para não depender de arquivo externo.
                    with open(img, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    corpo = f'<img src="data:image/png;base64,{b64}" alt="">'
                else:
                    corpo = f'<div class="quadro-emoji">{emoji}</div>'
                st.markdown(
                    f'<div class="quadro-card">{corpo}'
                    f'<div class="quadro-tipo">{html.escape(tipo)}</div>'
                    f'<div class="quadro-qtd">{qtd}</div></div>',
                    unsafe_allow_html=True,
                )
                if ao_filtrar is not None:
                    st.button(
                        "🔎 Filtrar",
                        key=f"quadro_filtrar_{i}_{col_tipo}_{tipo}",
                        use_container_width=True,
                        help=f"Filtrar a página pelo tipo {tipo}",
                        on_click=ao_filtrar,
                        args=(tipo,),
                    )


def bar(df: pd.DataFrame, x: str, y: str, title: str, horizontal: bool = False, top: int | None = None, custom_data=None):
    """Gráfico de barras padronizado com paleta, rótulos e ordem correta.

    Em barras horizontais, o Plotly coloca a 1ª categoria na base do eixo Y;
    `categoryorder="total ascending"` deixa o maior valor no topo.
    """
    d = df.copy()
    if top:
        d = d.head(top)
    if horizontal:
        fig = px.bar(d, x=y, y=x, orientation="h", title=title, custom_data=custom_data)
        fig.update_yaxes(categoryorder="total ascending")
    else:
        fig = px.bar(d, x=x, y=y, title=title, custom_data=custom_data)
    colorir_barras(fig, len(d))
    return theme_fig(rotular_barras(fig, d[y]))


def linha(df: pd.DataFrame, x: str, y: str, title: str, custom_data=None):
    """Gráfico de linhas com marcadores (ex.: evolução mensal)."""
    fig = px.line(df, x=x, y=y, title=title, markers=True, custom_data=custom_data)
    return theme_fig(fig)


def set_filtro(chave: str):
    """Retorna callable que define `st.session_state[chave]` — usado no clique-para-filtrar.

    O valor é convertido para string para bater com as opções de `opcoes()`.
    """

    def _aplicar(valor):
        st.session_state[chave] = str(valor)

    return _aplicar


def plot_click(fig, chave: str, aplicar, **kwargs):
    """Exibe o gráfico com clique-para-filtrar.

    Quando um ponto é clicado, `aplicar(valor)` é chamado com o primeiro valor
    do `customdata` do ponto (fallback: eixo de categoria). Passe `custom_data`
    ao construir a figura para garantir o valor da dimensão filtrada.
    """
    def _ao_selecionar():
        # Evento de seleção gerado pelo Streamlit (atributo `selection`).
        ev = st.session_state.get(chave)
        if not ev:
            return
        sel = getattr(ev, "selection", None)
        if sel is None and isinstance(ev, dict):
            sel = ev.get("selection")
        pts = (sel or {}).get("points") or []
        if not pts:
            return
        p = pts[0]
        # Prefere o customdata (dimensão filtrada) e recua para o eixo.
        cd = p.get("customdata")
        if cd:
            valor = cd[0]
        elif p.get("y") is not None:
            valor = p["y"]
        else:
            valor = p.get("x")
        if valor is not None:
            aplicar(valor)

    st.plotly_chart(
        fig,
        on_select=_ao_selecionar,
        selection_mode="points",
        key=chave,
        width="stretch",
        **kwargs,
    )


def dataframe_estilizado(df: pd.DataFrame, colunas: dict | None = None):
    """Exibe um dataframe em largura total, sem o índice."""
    st.dataframe(df, column_config=colunas, width="stretch", hide_index=True)


def converter_datas(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    """Copia o DataFrame convertendo colunas datetime para `dd/mm/yyyy hh:mm`.

    O `DatetimeColumn(format=...)` não respeita o formato no Streamlit 1.60
    (mostra ISO), então a conversão é feita direto na string exibida. O df
    original não é alterado (a coluna original segue para o PDF).
    """
    out = df.copy()
    for c in colunas:
        if c in out.columns and pd.api.types.is_datetime64_any_dtype(out[c]):
            out[c] = out[c].apply(lambda v: v.strftime("%d/%m/%Y %H:%M") if pd.notna(v) else "")
    return out


def _limpar_cache():
    """Limpa o cache de todas as consultas (usado ao importar/atualizar base)."""
    import queries

    for fn in (
        queries._frota,
        queries._gastos,
        queries._diesel,
        queries._etanol,
        queries._estoque,
        queries._nf_diesel,
        queries._veiculos_leves,
    ):
        try:
            fn.clear()
        except Exception:
            pass


def _limpar_filtros(chaves: list[str]):
    """Callback usado no botão de limpar filtros (roda antes do script)."""
    for k in chaves:
        st.session_state[k] = "Todos"


def sidebar_acoes(
    titulo_relatorio: str,
    figs: list[tuple[str, "go.Figure"]],
    tabela_pdf: pd.DataFrame | None = None,
    periodo: str = "",
    nome_arquivo: str = "relatorio.pdf",
    chave: str = "relatorio",
    chaves_filtro: list[str] | None = None,
):
    """Botões de ação fixados na barra lateral, abaixo dos filtros.

    - Limpar filtros: aparece quando há filtros ativos (inclusive os aplicados
      pelo clique nos gráficos) e volta todos para "Todos".
    - Importar base: permite carregar uma nova `base.xlsx` em sessão.
    - Atualizar dados: limpa o cache das consultas e recarrega a base.
    - Gerar PDF: monta um relatório com os gráficos e o detalhamento dos dados.
    """
    from relatorio import gerar_pdf

    # Chave na sessão onde os bytes do PDF gerado ficam guardados até baixar.
    estado_pdf = f"_{chave}_pdf_bytes"

    with st.sidebar:
        if chaves_filtro and any(
            st.session_state.get(k, "Todos") != "Todos" for k in chaves_filtro
        ):
            st.button(
                "🧹 Limpar filtros",
                use_container_width=True,
                help='Volta todos os filtros (inclusive os clicados nos gráficos) para "Todos".',
                on_click=_limpar_filtros,
                args=(chaves_filtro,),
            )
        st.divider()
        sidebar_importar_base()
        st.divider()
        if st.button("🔄 Atualizar dados", use_container_width=True, help="Recarrega os dados da planilha base."):
            _limpar_cache()
            st.rerun()
        if st.button("📄 Gerar PDF", use_container_width=True, help="Gera um relatório com os gráficos e o detalhamento dos dados."):
            with st.spinner("Gerando relatório..."):
                try:
                    st.session_state[estado_pdf] = gerar_pdf(
                        titulo_relatorio,
                        figs,
                        tabela_pdf,
                        periodo=periodo,
                        nome_arquivo=nome_arquivo,
                    )
                except Exception as exc:
                    st.session_state[estado_pdf] = None
                    st.error(f"Falha ao gerar o PDF: {exc}")
        if st.session_state.get(estado_pdf):
            st.download_button(
                "⬇️ Baixar PDF",
                data=st.session_state[estado_pdf],
                file_name=nome_arquivo,
                mime="application/pdf",
                use_container_width=True,
            )


def sidebar_importar_base():
    """Importa uma nova `base.xlsx` e atualiza os dados imediatamente.

    Funciona localmente e no Cloud (Streamlit Community): o arquivo fica na
    sessão (em memória), sem precisar gravar nada em disco. Enviar outro
    arquivo substitui a base em uso.
    """
    # Mensagem de confirmação exibida uma única vez após a importação.
    if st.session_state.pop("_base_importada_msg", False):
        st.success("Base importada! Dados atualizados em todos os dashboards.")

    # Usuário sem permissão só vê o aviso e não o widget de upload.
    if not permissao("pode_importar"):
        st.caption("Sem permissão para importar a base — solicite a um administrador.")
        return

    if "importar_base_ativo" not in st.session_state:
        st.session_state["importar_base_ativo"] = False
    st.toggle(
        "📥 Importar base",
        key="importar_base_ativo",
        help="Carregue uma nova base.xlsx e os dashboards passam a usar os dados dela imediatamente.",
    )
    if not st.session_state["importar_base_ativo"]:
        return

    arquivo = st.file_uploader(
        "Selecione o arquivo `base.xlsx`",
        type=["xlsx"],
        key="importar_base_arquivo",
    )
    if arquivo is None:
        st.caption("Envie uma nova base sempre que quiser atualizar os dados.")
        return

    dados = arquivo.getvalue()
    import hashlib

    # Evita reprocessar o mesmo arquivo já enviado.
    hash_arquivo = hashlib.sha256(dados).hexdigest()
    if hash_arquivo == st.session_state.get("_base_ultimo_hash"):
        return

    # Valida o arquivo: precisa ser .xlsx com as abas obrigatórias.
    try:
        abas = dl.sheets_do_arquivo(dados)
    except Exception:
        abas = []
    if not abas:
        st.error("Não foi possível ler o arquivo. Envie um `.xlsx` válido no mesmo modelo da base atual.")
        return

    faltando = [s for s in dl.SHEETS_REQUERIDAS if s not in abas]
    if faltando:
        st.error("O arquivo não contém as abas obrigatórias: " + ", ".join(f"`{s}`" for s in faltando))
        return

    # Guarda os bytes na sessão, limpa o cache das consultas e recarrega.
    st.session_state["_base_fonte"] = dados
    st.session_state["_base_ultimo_hash"] = hash_arquivo
    _limpar_cache()
    st.session_state["_base_importada_msg"] = True
    st.rerun()


def base_carregada() -> bool:
    """True quando há base em memória (upload) ou o arquivo padrão existe em disco."""
    if st.session_state.get("_base_fonte"):
        return True
    return dl.BASE_PATH.exists()


def prompt_sem_base(mostrar_upload: bool = True):
    """Aviso quando não há base disponível (ex.: Streamlit Cloud sem `dados/base.xlsx`).

    `mostrar_upload=False` deve ser usado onde o importador já está na barra
    lateral (ex.: página Início), evitando widget duplicado.
    """
    if permissao("pode_importar"):
        st.warning(
            "Nenhuma base de dados disponível no momento. "
            "Use a opção **📥 Importar base** (barra lateral) para carregar o `base.xlsx` "
            "da sua máquina e liberar os dashboards."
        )
        if mostrar_upload:
            sidebar_importar_base()
    else:
        st.warning(
            "Nenhuma base de dados disponível no momento e seu usuário não tem "
            "permissão para importá-la. Solicite a um administrador que carregue o `base.xlsx`."
        )
    st.stop()
