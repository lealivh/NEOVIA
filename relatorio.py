import re
from datetime import datetime
from io import BytesIO

import pandas as pd
from PIL import Image as PILImage
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ui_helpers import BRAND, LOGO_PATH

PAGE_W, PAGE_H = A4
MARGIN = 35
MAX_LINHAS_TABELA = 40
FONTE_CEL = "Helvetica"
TAMANHO_CEL = 8
RE_QUEBRA_COMMA = re.compile(r",(?=[A-Za-zÀ-ú(])")
RE_QUEBRA_ABRE = re.compile(r"\((?=[^ )])")
RE_QUEBRA_FECHA = re.compile(r"(?<=[^\s(])\)")


def _fmt_br(v: float, dec: int = 2) -> str:
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def montar_tabela(df: pd.DataFrame, colunas: list[str], formatos: dict) -> pd.DataFrame:
    """Prepara a tabela de detalhamento para o PDF.

    colunas: nomes originais na ordem desejada.
    formatos: dict {col: (label, tipo)} com tipo em date, datetime, brl, num, int ou str.
    Valores não convertíveis são mantidos como texto.
    """
    out = pd.DataFrame(index=df.index)
    for col in colunas:
        if col not in df.columns:
            continue
        label, tipo = formatos.get(col, (col, "str"))
        s = df[col]
        if tipo == "date":
            vals = [v.strftime("%d/%m/%Y") if pd.notna(v) else "" for v in s]
        elif tipo == "datetime":
            vals = [v.strftime("%d/%m/%Y %H:%M") if pd.notna(v) else "" for v in s]
        elif tipo in ("brl", "num", "int"):
            dec = 0 if tipo == "int" else 2
            prefixo = "R$ " if tipo == "brl" else ""
            vals = []
            for v in s:
                if pd.notna(v):
                    try:
                        vals.append(prefixo + _fmt_br(float(v), dec))
                    except (TypeError, ValueError):
                        vals.append(str(v))
                else:
                    vals.append("")
        else:
            vals = [str(v) if pd.notna(v) else "" for v in s]
        out[label] = vals
    return out


def _quebrar_nao_espacos(v: object) -> str:
    """Insere quebras de palavra em tokens sem espaço (vírgulas/parênteses).

    Protege decimais brasileiros ("112.683,00" permanece intacto) e datas.
    Ex.: "CONSERVAÇÃO(0001-24)MATRIZ" -> "CONSERVAÇÃO (0001-24) MATRIZ".
    """
    s = str(v)[:80]
    s = RE_QUEBRA_COMMA.sub(", ", s)
    s = RE_QUEBRA_ABRE.sub("( ", s)
    s = RE_QUEBRA_FECHA.sub(" )", s)
    return s


def _maior_palavra(vals: list[str], bold: bool = False) -> float:
    """Maior largura (em pontos) de uma palavra entre os valores."""
    font = "Helvetica-Bold" if bold else FONTE_CEL
    maior = 0.0
    for v in vals:
        for w in _quebrar_nao_espacos(v).split():
            maior = max(maior, stringWidth(w, font, TAMANHO_CEL))
    return maior


def _larguras_colunas(dados: pd.DataFrame, doc_width: float) -> tuple[list[float], bool]:
    """Largura por coluna suficiente para a maior palavra (sem cortes).

    Retorna (larguras, split) — `split=True` só se mesmo sem margens alguma
    coluna for mais estreita que sua maior palavra (caso extremo).
    """
    maior = []
    for col in dados.columns:
        header = max(_maior_palavra([col], bold=True), 10.0)
        corpo = _maior_palavra(list(dados[col]))
        maior.append(max(28.0, header, corpo))

    def com_pad(pad: float) -> list[float]:
        return [w + pad for w in maior]

    larguras = com_pad(10.0)
    if sum(larguras) > doc_width:
        larguras = com_pad(0.0)
    if sum(larguras) <= doc_width:
        return larguras, False
    fator = doc_width / sum(larguras)
    return [max(24.0, w * fator) for w in larguras], True


def _tabela_pdf(dados: pd.DataFrame, doc_width: float, max_linhas: int, st_sec, st_cap) -> list:
    colunas_pdf = list(dados.columns)
    larguras, split = _larguras_colunas(dados, doc_width)
    kwargs = {"splitLongWords": split, "breakLongWords": split}
    st_cel = ParagraphStyle(
        "cel",
        fontName=FONTE_CEL,
        fontSize=TAMANHO_CEL,
        leading=TAMANHO_CEL + 2,
        **kwargs,
    )
    st_cel_b = ParagraphStyle("celb", parent=st_cel, fontName="Helvetica-Bold", textColor=colors.white)
    header = [Paragraph(_quebrar_nao_espacos(c), st_cel_b) for c in colunas_pdf]
    linhas = [
        [Paragraph(_quebrar_nao_espacos(c), st_cel) for c in row]
        for row in dados.itertuples(index=False, name=None)
    ]
    tbl = Table([header] + linhas, repeatRows=1, colWidths=larguras)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND["vermelho"])),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(BRAND["cinza_claro"])),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(BRAND["cinza_claro"])]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    items = [Paragraph("Detalhamento dos dados", st_sec), tbl]
    if len(dados) > max_linhas:
        items.append(Paragraph(f"Exibidas as {max_linhas} primeiras linhas de {len(dados)}.", st_cap))
    return items


def _png_figura(fig):
    """Renderiza a figura em PNG via kaleido; retorna bytes ou None.

    Tenta 2x — a primeira chamada do kaleido pode falhar enquanto baixa o
    Chromium embutido (comum no primeiro uso / Cloud). Em vez de descartar
    o gráfico em silêncio, retorna None para o chamador avisar no PDF.
    """
    for tentativa in (1, 2):
        try:
            return fig.to_image(format="png", width=1400, height=650, scale=2)
        except Exception:
            if tentativa == 2:
                return None
    return None


def gerar_pdf(
    titulo: str,
    figs: list[tuple[str, "go.Figure"]],
    tabela_pdf: pd.DataFrame | None = None,
    periodo: str = "",
    nome_arquivo: str = "relatorio.pdf",
    logo_path=LOGO_PATH,
    max_linhas: int = MAX_LINHAS_TABELA,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=nome_arquivo,
        author="Neovia",
    )

    st_titulo = ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=16, leading=20, spaceAfter=2)
    st_sub = ParagraphStyle("sub", fontName="Helvetica", fontSize=9, leading=12, textColor=colors.grey)
    st_sec = ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=13, leading=16, spaceBefore=14, spaceAfter=6)
    st_fig = ParagraphStyle("fig", fontName="Helvetica-Bold", fontSize=11, leading=14, spaceBefore=10, spaceAfter=4)
    st_cap = ParagraphStyle("cap", fontName="Helvetica", fontSize=8, leading=10, textColor=colors.grey, spaceBefore=4)

    story = []
    if logo_path and logo_path.exists():
        try:
            logo = Image(str(logo_path))
            logo._restrictSize(220, 55)
            story.append(logo)
        except Exception:
            pass
    story.append(Paragraph(titulo, st_titulo))
    rodape_txt = f"Gerado em {datetime.now():%d/%m/%Y %H:%M}"
    if periodo:
        rodape_txt += f"  ·  Período analisado: {periodo}"
    story.append(Paragraph(rodape_txt, st_sub))
    story.append(Spacer(1, 6))

    for nome, fig in figs:
        png = _png_figura(fig)
        if png is None:
            story.append(Paragraph(f"{nome} — gráfico não pôde ser gerado nesta execução.", st_cap))
            continue
        im = PILImage.open(BytesIO(png))
        w, h = im.size
        ratio = min(doc.width / w, 400 / h)
        img = Image(BytesIO(png), width=w * ratio, height=h * ratio)
        story.append(KeepTogether([Paragraph(nome, st_fig), img]))

    doc.build(story)

    if tabela_pdf is not None and len(tabela_pdf):
        dados = tabela_pdf.head(max_linhas)
        margem_tab = 25
        buf_tab = BytesIO()
        doc_tab = SimpleDocTemplate(
            buf_tab,
            pagesize=landscape(A4),
            rightMargin=margem_tab,
            leftMargin=margem_tab,
            topMargin=margem_tab,
            bottomMargin=margem_tab,
            title=nome_arquivo,
            author="Neovia",
        )
        story_tab = _tabela_pdf(dados, doc_tab.width, max_linhas, st_sec, st_cap)
        doc_tab.build(story_tab)
        final = BytesIO()
        writer = PdfWriter()
        writer.append(PdfReader(BytesIO(buf.getvalue())))
        writer.append(PdfReader(BytesIO(buf_tab.getvalue())))
        writer.write(final)
        return final.getvalue()

    return buf.getvalue()
