"""Controle de acesso do portal.

Usuários ficam em `usuarios.json` (senhas com hash pbkdf2 + sal). Cada usuário
tem as permissões:
  - pode_visualizar: libera os dashboards;
  - pode_importar:   libera o upload de uma nova base.xlsx;
  - admin:           acesso ao gerenciamento de usuários na barra lateral.

Se o arquivo não existir, um usuário `admin` padrão é criado automaticamente
(senha exibida uma única vez na interface).
"""
import hashlib
import hmac
import json
import secrets
from pathlib import Path

import streamlit as st

import gist_sync

ARQUIVO_USUARIOS = Path(__file__).parent / "usuarios.json"
ADMIN_PADRAO = "admin"
SENHA_PADRAO = "neovia2026"
_ITERACOES = 200_000
_ALGORITMO = "sha256"


def _gerar_sal() -> str:
    return secrets.token_hex(16)


def _hash_senha(senha: str, sal: str) -> str:
    dk = hashlib.pbkdf2_hmac(_ALGORITMO, senha.encode("utf-8"), bytes.fromhex(sal), _ITERACOES)
    return dk.hex()


def _registro(senha: str, pode_visualizar: bool, pode_importar: bool, admin: bool = False) -> dict:
    sal = _gerar_sal()
    return {
        "sal": sal,
        "hash": _hash_senha(senha, sal),
        "pode_visualizar": pode_visualizar,
        "pode_importar": pode_importar,
        "admin": admin,
    }


def carregar_usuarios() -> dict:
    """Lê o arquivo de usuários; se não existir, busca no Gist (Cloud) ou cria o
    admin padrão na primeira execução."""
    if ARQUIVO_USUARIOS.exists():
        return json.loads(ARQUIVO_USUARIOS.read_text(encoding="utf-8"))
    remoto = gist_sync.carregar()
    if remoto:
        salvar_usuarios(remoto)
        return remoto
    usuarios = {ADMIN_PADRAO: _registro(SENHA_PADRAO, True, True, admin=True)}
    salvar_usuarios(usuarios)
    try:
        st.session_state["_usuarios_criados_padrao"] = True
    except Exception:
        pass
    return usuarios


def salvar_usuarios(usuarios: dict):
    ARQUIVO_USUARIOS.write_text(json.dumps(usuarios, ensure_ascii=False, indent=2), encoding="utf-8")
    gist_sync.salvar(usuarios)


def autenticar(usuario: str, senha: str) -> bool:
    reg = carregar_usuarios().get(usuario.strip())
    if not reg or not senha:
        return False
    return hmac.compare_digest(_hash_senha(senha, reg["sal"]), reg["hash"])


def criar_usuario(usuario: str, senha: str, pode_visualizar: bool = True, pode_importar: bool = False, admin: bool = False):
    usuarios = carregar_usuarios()
    usuarios[usuario.strip()] = _registro(senha, pode_visualizar, pode_importar, admin)
    salvar_usuarios(usuarios)


def alterar_senha(usuario: str, nova_senha: str):
    usuarios = carregar_usuarios()
    reg = usuarios.get(usuario.strip())
    if not reg:
        return False
    sal = _gerar_sal()
    reg["sal"] = sal
    reg["hash"] = _hash_senha(nova_senha, sal)
    salvar_usuarios(usuarios)
    return True


def remover_usuario(usuario: str):
    usuarios = carregar_usuarios()
    usuarios.pop(usuario.strip(), None)
    salvar_usuarios(usuarios)


def usuario_atual() -> str | None:
    return st.session_state.get("_usuario")


def permissao(perm: str) -> bool:
    u = usuario_atual()
    if not u:
        return False
    return bool(carregar_usuarios().get(u, {}).get(perm, False))


def fazer_logout():
    for k in ("_usuario",):
        st.session_state.pop(k, None)


def _gerenciar_usuarios():
    """Painel (somente admin) para cadastrar/remover usuários e trocar senha."""
    usuarios = carregar_usuarios()
    with st.expander("👥 Gerenciar usuários"):
        if not gist_sync.configurado():
            st.warning(
                "⚠️ Persistência no GitHub não configurada. No Streamlit Cloud os usuários "
                "criados aqui se perdem quando o app reinicia — configure `github.token` "
                "em **Settings → Secrets** do Streamlit Cloud."
            )
        st.caption(f"{len(usuarios)} usuário(s) cadastrado(s):")
        for nome, reg in sorted(usuarios.items()):
            marcacoes = []
            if reg.get("admin"):
                marcacoes.append("admin")
            if reg.get("pode_visualizar"):
                marcacoes.append("visualizar")
            if reg.get("pode_importar"):
                marcacoes.append("importar")
            st.caption(f"• **{nome}** — {', '.join(marcacoes) or 'sem permissões'}")
        st.divider()
        st.markdown("**Novo usuário**")
        novo = st.text_input("Usuário", key="adm_novo_usuario")
        nova_senha = st.text_input("Senha", type="password", key="adm_novo_senha")
        c1, c2, c3 = st.columns(3)
        perm_v = c1.checkbox("Visualizar", value=True, key="adm_novo_visualizar")
        perm_i = c2.checkbox("Importar base", key="adm_novo_importar")
        perm_a = c3.checkbox("Admin", key="adm_novo_admin")
        if st.button("Criar usuário", use_container_width=True, key="adm_novo_btn"):
            if not novo.strip() or not nova_senha:
                st.warning("Informe usuário e senha.")
            elif novo.strip() in usuarios:
                st.warning("Usuário já existe.")
            else:
                criar_usuario(novo, nova_senha, perm_v, perm_i, perm_a)
                st.success(f"Usuário **{novo.strip()}** criado.")
                st.rerun()
        st.divider()
        st.markdown("**Alterar senha / remover**")
        alvo = st.selectbox("Usuário", sorted(usuarios.keys()), key="adm_alvo")
        troca = st.text_input("Nova senha", type="password", key="adm_nova_senha")
        if st.button("Alterar senha", use_container_width=True, key="adm_troca_btn"):
            if troca:
                alterar_senha(alvo, troca)
                st.success("Senha alterada.")
        if st.button("Remover usuário", use_container_width=True, key="adm_remover_btn"):
            if alvo == usuario_atual():
                st.warning("Você não pode remover o próprio usuário.")
            else:
                remover_usuario(alvo)
                st.success(f"Usuário **{alvo}** removido.")
                st.rerun()


def painel_login():
    """Formulário de login na barra lateral. Retorna o usuário logado (ou None)."""
    u = usuario_atual()
    with st.sidebar:
        st.header("🔐 Acesso")
        if st.session_state.pop("_usuarios_criados_padrao", False):
            st.warning(f"Usuário padrão criado: **{ADMIN_PADRAO}** / senha `{SENHA_PADRAO}` — altere a senha.")
        if u:
            st.caption(f"Logado: **{u}**")
            if st.button("Sair", use_container_width=True, key="btn_sair"):
                fazer_logout()
                st.rerun()
            if permissao("admin"):
                _gerenciar_usuarios()
            return u
        st.text_input("Usuário", key="login_usuario")
        st.text_input("Senha", type="password", key="login_senha")
        if st.button("Entrar", type="primary", use_container_width=True, key="btn_entrar"):
            usuario = st.session_state.get("login_usuario", "")
            senha = st.session_state.get("login_senha", "")
            if autenticar(usuario, senha):
                st.session_state["_usuario"] = usuario.strip()
                st.session_state.pop("login_senha", None)
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
    return None


def exigir_login():
    """Bloqueia a página enquanto não houver usuário logado com acesso.

    Deve ser chamado logo após `st.set_page_config` (ex.: dentro de `set_page`).
    Exibe o painel de login na barra lateral e, sem autenticação ou sem a
    permissão de visualizar, mostra aviso no corpo e chama `st.stop()`.
    """
    u = painel_login()
    if u is None:
        st.warning("🔒 Faça login na barra lateral para acessar os dashboards.")
        st.stop()
    if not permissao("pode_visualizar"):
        st.warning("🚫 Você não tem permissão para visualizar os dashboards.")
        if st.button("Sair"):
            fazer_logout()
            st.rerun()
        st.stop()
