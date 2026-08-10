import streamlit as st

import data_loader as dl


def _fonte():
    """Fonte da base: bytes do upload em sessão ou o arquivo padrão da pasta `dados/`."""
    fonte = st.session_state.get("_base_fonte")
    if isinstance(fonte, bytes):
        return fonte
    return None


@st.cache_data(show_spinner="Carregando frota...", ttl=3600)
def _frota(fonte):
    return dl.load_equipamentos(fonte)


@st.cache_data(show_spinner="Carregando gastos...", ttl=3600)
def _gastos(fonte):
    return dl.load_gastos(fonte)


@st.cache_data(show_spinner="Carregando consumo diesel...", ttl=3600)
def _diesel(fonte):
    return dl.load_diesel(fonte)


@st.cache_data(show_spinner="Carregando consumo veículos leves...", ttl=3600)
def _etanol(fonte):
    return dl.load_etanol(fonte)


@st.cache_data(show_spinner="Carregando estoque...", ttl=3600)
def _estoque(fonte):
    return dl.load_estoque(fonte)


@st.cache_data(show_spinner="Carregando NF diesel...", ttl=3600)
def _nf_diesel(fonte):
    return dl.load_nf_diesel(fonte)


@st.cache_data(show_spinner="Carregando veículos leves...", ttl=3600)
def _veiculos_leves(fonte):
    return dl.load_veiculos_leves(fonte)


def frota():
    return _frota(_fonte())


def gastos():
    return _gastos(_fonte())


def diesel():
    return _diesel(_fonte())


def etanol():
    return _etanol(_fonte())


def estoque():
    return _estoque(_fonte())


def nf_diesel():
    return _nf_diesel(_fonte())


def veiculos_leves():
    return _veiculos_leves(_fonte())
