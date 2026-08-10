import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

BASE_PATH = Path(__file__).parent / "dados" / "base.xlsx"

EXCEL_EPOCH = datetime(1899, 12, 30)
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

# numFmtIds considerados datas/datetimes
DATE_FMT_IDS = {14, 15, 16, 17, 18, 19, 20, 21, 22, 45, 46, 47, 165}
TIME_FMT_IDS = {44}


def _read_xml(zf: zipfile.ZipFile, name: str) -> ET.Element:
    return ET.fromstring(zf.read(name))


def _load_workbook_xml(path: Path):
    with zipfile.ZipFile(path) as zf:
        style_root = _read_xml(zf, "xl/styles.xml")
        xfs = style_root.find("m:cellXfs", NS)
        num_fmts = {
            int(f.get("numFmtId")): f.get("formatCode")
            for f in style_root.findall("m:numFmts/m:numFmt", NS)
        }
        sst_root = _read_xml(zf, "xl/sharedStrings.xml")
        shared = [
            "".join(t.text or "" for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
            for si in sst_root.findall("m:si", NS)
        ]
        wb_root = _read_xml(zf, "xl/workbook.xml")
        sheets = [
            (s.get("name"), s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"))
            for s in wb_root.findall("m:sheets/m:sheet", NS)
        ]
        rels = _read_xml(zf, "xl/_rels/workbook.xml.rels")
        rel_map = {
            r.get("Id"): r.get("Target")
            for r in rels.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
        }
        sheet_names = {}
        for name, rid in sheets:
            sheet_names[name] = "xl/" + rel_map[rid] if not rel_map[rid].startswith("xl/") else rel_map[rid]
    return style_root, xfs, num_fmts, shared, sheet_names


def _cell_value(cell, xfs, num_fmts, shared) -> object:
    t = cell.get("t")
    if t == "inlineStr":
        is_node = cell.find("m:is", NS)
        if is_node is None:
            return None
        return "".join(tn.text or "" for tn in is_node.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
    v_node = cell.find("m:v", NS)
    if v_node is None or v_node.text is None:
        return None
    raw = v_node.text
    if t == "s":
        return shared[int(raw)]
    if t == "str":
        return raw
    try:
        num = float(raw)
    except ValueError:
        return raw
    if num == int(num):
        ival = int(num)
    else:
        ival = None
    style_idx = cell.get("s")
    fmt_id = 0
    if style_idx is not None and xfs is not None:
        xf = xfs.findall("m:xf", NS)[int(style_idx)]
        fmt_id = int(xf.get("numFmtId"))
    if fmt_id in DATE_FMT_IDS:
        return EXCEL_EPOCH + timedelta(days=num)
    if fmt_id in TIME_FMT_IDS and num < 1:
        return (datetime(1899, 12, 31) + timedelta(days=num)).time()
    if ival is not None:
        return ival
    return num


def _sheet_to_df(path: Path, sheet_name: str):
    _, xfs, num_fmts, shared, sheet_names = _load_workbook_xml(path)
    with zipfile.ZipFile(path) as zf:
        root = _read_xml(zf, sheet_names[sheet_name])
    rows = []
    for row in root.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
        cells = {}
        for c in row.findall("m:c", NS):
            col_ref = c.get("r")
            col_letter = "".join(ch for ch in col_ref if ch.isalpha()) if col_ref else None
            cells[col_letter] = _cell_value(c, xfs, num_fmts, shared)
        rows.append(cells)
    if not rows:
        return pd.DataFrame()
    max_cols = max(len(r) for r in rows)
    ordered = []
    for r in rows:
        row_vals = [None] * max_cols
        for k, v in r.items():
            if k:
                idx = ord(k[0]) - ord("A")
                if 0 <= idx < max_cols:
                    row_vals[idx] = v
        ordered.append(row_vals)
    df = pd.DataFrame(ordered[1:], columns=[str(h).strip().replace("\n", " ") if h is not None else "" for h in ordered[0]])
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def _load_sheet(name: str, rename: dict | None = None, date_cols: list[str] | None = None) -> pd.DataFrame:
    df = _sheet_to_df(BASE_PATH, name)
    if rename:
        df = df.rename(columns=rename)
        df = df[[c for c in rename.values() if c in df.columns]]
    for col in date_cols or []:
        if col in df.columns:
            df[col] = _to_datetime(df[col])
    return df


def _to_datetime(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series)
    numeric = pd.to_numeric(series, errors="coerce")
    conv = pd.to_datetime(
        EXCEL_EPOCH + pd.to_timedelta(numeric.where(numeric.between(1, 75_000)), unit="D"),
        errors="coerce",
    )
    if pd.api.types.is_numeric_dtype(series):
        return conv
    dt_str = pd.to_datetime(series, errors="coerce")
    return dt_str.mask(numeric.notna(), conv)


def load_equipamentos() -> pd.DataFrame:
    df = _load_sheet(
        "EQUIPAMENTOS",
        {
            "PREFIXO": "prefixo",
            "SITUAÇÃO": "situacao",
            "STATUS": "status",
            "EQUIPE": "equipe",
            "CLASSE OPERACIONAL": "classe_operacional",
            "MARCA": "marca",
            "MOD.": "modelo",
            "ANO": "ano",
            "CHASSI/SERIE": "chassi",
            "PLACA": "placa",
            "LOCADOR": "locador",
            "CONTRATO": "contrato",
            "VALOR": "valor",
            "DATA MOB.": "data_mobilizacao",
            "DATA ENTRADA": "data_entrada",
            "DESMOB.": "data_desmobilizacao",
        },
        date_cols=["data_mobilizacao", "data_entrada", "data_desmobilizacao"],
    )
    return df


def load_gastos() -> pd.DataFrame:
    df = _load_sheet(
        "GASTOS",
        {
            "DATA NF": "data_nf",
            "N° NF": "numero_nf",
            "Valor": "valor",
            "CNPJ": "cnpj",
            "Fornecedor": "fornecedor",
            "Aplicação": "aplicacao",
            "Classe Manut.": "classe_manut",
            "Vencimento": "vencimento",
            "Custo (Desconto medição)": "custo_medicao",
            "Grupo Aplicação": "grupo_aplicacao",
            "Equipe": "equipe",
            "Obs.": "obs",
            "Adm": "adm",
            "Locadora": "locadora",
            "Grupo Fornecedor": "grupo_fornecedor",
            "Conf": "conf",
        },
        date_cols=["data_nf", "vencimento", "adm"],
    )
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    return df


def load_diesel() -> pd.DataFrame:
    return _load_sheet(
        "CONSUMO DIESEL EQUIPAMENTOS",
        {
            "Espécie": "especie",
            "Cód.": "cod",
            "Empresa/Terceiro": "empresa",
            "Cód.2": "prefixo",
            "Equipamento": "equipamento",
            "Data Hora": "data_hora",
            "Cód.3": "cod3",
            "Ponto": "ponto",
            "Material": "material",
            "Quantidade": "quantidade",
            "Valor": "valor",
            "Medição@Anterior": "medicao_anterior",
            "Medição@Atual": "medicao_atual",
            "Uso": "uso",
            "Consumo": "consumo",
        },
        date_cols=["data_hora"],
    )


def load_etanol() -> pd.DataFrame:
    return _load_sheet(
        "CONSUMO VEICULOS LEVES ETANOL",
        {
            "CODIGO TRANSACAO": "codigo_transacao",
            "FORMA DE PAGAMENTO": "forma_pagamento",
            "CODIGO CLIENTE": "codigo_cliente",
            "NOME REDUZIDO": "nome_reduzido",
            "DATA TRANSACAO": "data_transacao",
            "PLACA": "placa",
            "TIPO FROTA": "tipo_frota",
            "MODELO VEICULO": "modelo",
            "NUMERO FROTA": "numero_frota",
            "ANO": "ano",
            "MATRICULA": "matricula",
            "NOME MOTORISTA": "motorista",
            "SERVICO": "servico",
            "TIPO COMBUSTIVEL": "combustivel",
            "LITROS": "litros",
            "VL/LITRO": "vl_litro",
            "HODOMETRO OU HORIMETRO": "hodometro",
            "KM RODADOS OU HORAS TRABALHADA": "km_rodados",
            "KM/LITRO OU LITROS/HORA": "km_litro",
            "VALOR EMISSAO": "valor",
            "CODIGO ESTABELECIMENTO": "cod_estabelecimento",
            "NOME ESTABELECIMENTO": "estabelecimento",
            "TIPO ESTABELECIMENTO": "tipo_estabelecimento",
            "ENDERECO": "endereco",
            "BAIRRO": "bairro",
            "CIDADE": "cidade",
            "UF": "uf",
            "INFORMACAO ADIDIONAL 1": "info1",
            "INFORMACAO ADIDIONAL 2": "info2",
            "INFORMACAO ADIDIONAL 3": "info3",
            "INFORMACAO ADIDIONAL 4": "info4",
            "INFORMACAO ADIDIONAL 5": "info5",
            "FORMA TRANSACAO": "forma_transacao",
            "CODIGO LIBERACAO RESTRICAO": "cod_liberacao",
            "SERIE POS": "serie_pos",
            "NUMERO CARTAO": "numero_cartao",
            "FAMILIA VEICULO": "familia",
            "GRUPO RESTRICAO": "grupo_restricao",
            "CODIGO EMISSORA": "cod_emissora",
            "RESPONSAVEL": "responsavel",
            "TIPO ENTRADA HODOMETRO": "tipo_entrada_hodometro",
        },
        date_cols=["data_transacao"],
    )


def load_estoque() -> pd.DataFrame:
    return _load_sheet("ESTOQUE")


def load_nf_diesel() -> pd.DataFrame:
    return _load_sheet(
        "NF DIESEL ENTRADAS",
        {
            "Fornecedor": "fornecedor",
            "Data / Hora": "data_hora",
            "Documento": "documento",
            "Série": "serie",
            "Vl Total NF": "valor_total",
            "Pto": "pto",
            "Comb.@Lubri.": "comb_lubri",
            "Tanq.": "tanque",
            "Quantidade": "quantidade",
            "Valor Unit.": "valor_unitario",
        },
        date_cols=["data_hora"],
    )


def load_veiculos_leves() -> pd.DataFrame:
    return _load_sheet(
        "VEICULOS LEVES",
        {
            "LOCADORA": "locadora",
            "CONTATO": "contato",
            "LOCAÇÃO MÊS": "locacao_mes",
            "PLACA": "placa",
            "MODELO": "modelo",
            "SETOR": "setor",
            "RESPONSÁVEL": "responsavel",
        },
    )


def norm_empresa(s) -> str:
    """Normaliza a empresa/terceiro para exibição nos dashboards."""
    if s is None:
        return "Não informado"
    t = str(s).strip()
    if t in ("", "-"):
        return "Não informado"
    up = t.upper()
    if " - " in up:
        up = up.split(" - ")[0].strip()
    alias = {
        "NEOVIA": "Neovia",
        "NEOVIA CONST. (NEO)": "Neovia",
        "TERCEIROS": "Terceiros",
        "MAÇARICO/TERCEIROS": "Terceiros",
        "FRETEIRO": "Freteiro",
        "SO ROLOS": "Só Rolos",
        "LUG": "LUG Transportes",
        "CONST SCHOROEDER": "Schoroeder",
        "CONSTRUÇÕES SCHOROEDER EIRELI": "Schoroeder",
        "CONSTRUÇÕES SCHOROEDER": "Schoroeder",
        "EEL TRANSPORTES": "E&L Locações",
        "NOVA FROTA": "Nova Frota",
        "TRAC TEC": "Trac Tec",
        "ROLEPARTS": "Roleparts",
        "BOB MAQ": "Bob Maq",
        "BOBMAQUINAS": "Bob Maq",
        "TERRA CIVIL": "Terra Civil",
        "DSD LOCADORA": "DSD Locadora",
        "SUDOESTE": "Sudoeste",
        "M2 TRATORES": "M2 Tratores",
        "MANTOMAC": "Mantomac",
        "RECK TRANSPORTES": "Reck Transportes",
        "JOAO PB FERREIRA": "João PB Ferreira",
        "NENE TRANSPORTES": "Nenê Transportes",
        "NOVACAP": "Novacap",
        "OURO VERDE": "Ouro Verde",
        "ALBERTON": "Alberton",
        "BANCO BRASILEIRO": "Banco Brasileiro",
        "ANDREATTA": "Andreatta",
        "MUNDIAL HOME": "Mundial Home",
        "ERGOS": "Ergos",
        "JEM LOCADORA": "JEM Locadora",
        "BM RENTAL": "BM Rental",
        "TUTI": "Tuti",
        "CONSTRUBEM": "Construbem",
        "STRAPA": "Strapa",
        "EL LOCACOES": "EL Locações",
        "MACROMAQ": "Macromaq",
        "ELO DOIS": "Elo Dois",
        "DOIS IRMAOS": "Dois Irmãos",
        "FABIANE MARQUES": "Fabiane Marques",
        "BORTOTI": "Bortoti",
        "EXATO": "Exato",
        "ALTOMAX": "Altomax",
        "FOCO SOLUCOES": "Foco Soluções",
        "TRANS MARGATTO": "Trans Margatto",
        "EGT": "Egt",
        "NEXEED": "Nexeed",
        "MILK & SANTOS": "Milk & Santos",
        "DE AMORIM": "De Amorim",
        "JEREMIAS": "Jeremias",
        "CARNAUBA": "Carnaúba",
        "TV": "TV",
        "NEOVIA": "Neovia",
        "SUL": "Sul",
    }
    return alias.get(up, t.title() if not t.isupper() else t)
