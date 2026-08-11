"""Persistência de usuários num Gist privado do GitHub.

O Streamlit Cloud não tem disco persistente: o `usuarios.json` local é recriado
a cada deploy. Para os usuários sobreviverem a reinícios, o arquivo é espelhado
num Gist privado via API do GitHub (Gist não dispara novo deploy).

Configuração (`.streamlit/secrets.toml`, fora do git):

    [github]
    token = "ghp_xxxxxxxx"
    # gist_id é opcional: na primeira execução o app descobre/cria o gist sozinho
    # gist_id = "abc123..."

Também aceita as variáveis de ambiente `GITHUB_TOKEN` e `GIST_ID`.

Sem token configurado, o app usa apenas o arquivo local (funciona localmente,
onde o disco é persistente).
"""
import json
import os
import time
import urllib.request
from pathlib import Path

_API = "https://api.github.com"
_NOME_ARQUIVO = "usuarios.json"
_TTL = 30.0

_cache: list = [0.0, None]


def _ler_secrets() -> dict:
    """Seção `[github]` do secrets.toml. No `streamlit run` usa st.secrets;
    fora dele (CLI/bare mode) lê o arquivo diretamente."""
    try:
        import streamlit as st

        g = st.secrets.get("github", {})
        if g:
            return g
    except Exception:
        pass
    try:
        import tomllib

        p = Path(__file__).parent / ".streamlit" / "secrets.toml"
        if p.exists():
            return tomllib.loads(p.read_text(encoding="utf-8")).get("github", {})
    except Exception:
        pass
    return {}


def _token() -> str | None:
    t = _ler_secrets().get("token")
    if t:
        return str(t).strip() or None
    for var in ("GITHUB_TOKEN", "GITHUB_PAT", "GH_TOKEN"):
        valor = os.environ.get(var)
        if valor and valor.strip():
            return valor.strip()
    return None


def _gist_id_config() -> str | None:
    g = _ler_secrets().get("gist_id")
    if g:
        return str(g).strip()
    return os.environ.get("GIST_ID")


def configurado() -> bool:
    return bool(_token())


def _request(method: str, url: str, token: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "neovia-dashboards")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=data, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _descobrir_gist(token: str) -> str:
    """Retorna o id do gist que contém usuarios.json, criando-o se não existir."""
    config_id = _gist_id_config()
    if config_id:
        return config_id
    lista = _request("GET", f"{_API}/gists", token)
    for g in lista:
        if _NOME_ARQUIVO in g.get("files", {}):
            return g["id"]
    criado = _request(
        "POST",
        f"{_API}/gists",
        token,
        {
            "description": "Usuários do Portal de Dashboards Neovia",
            "public": False,
            "files": {_NOME_ARQUIVO: {"content": "{}"}},
        },
    )
    return criado["id"]


def carregar() -> dict | None:
    """Lê o dicionário de usuários do gist (com cache de 30s). None se indisponível."""
    token = _token()
    if not token:
        return None
    agora = time.time()
    if _cache[0] and agora - _cache[0] < _TTL:
        return _cache[1]
    try:
        gist_id = _descobrir_gist(token)
        g = _request("GET", f"{_API}/gists/{gist_id}", token)
        conteudo = g["files"].get(_NOME_ARQUIVO, {}).get("content", "{}")
        usuarios = json.loads(conteudo)
    except Exception:
        return None
    _cache[0] = agora
    _cache[1] = usuarios
    return usuarios


def salvar(usuarios: dict) -> bool:
    """Envia o dicionário de usuários ao gist. False se não configurado/falhar."""
    token = _token()
    if not token:
        return False
    try:
        gist_id = _descobrir_gist(token)
        _request(
            "PATCH",
            f"{_API}/gists/{gist_id}",
            token,
            {"files": {_NOME_ARQUIVO: {"content": json.dumps(usuarios, ensure_ascii=False, indent=2)}}},
        )
    except Exception:
        return False
    _cache[0] = time.time()
    _cache[1] = dict(usuarios)
    return True
