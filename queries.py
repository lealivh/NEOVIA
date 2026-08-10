import streamlit as st

import data_loader as dl


@st.cache_data(show_spinner="Carregando frota...", ttl=3600)
def frota():
    return dl.load_equipamentos()


@st.cache_data(show_spinner="Carregando gastos...", ttl=3600)
def gastos():
    return dl.load_gastos()


@st.cache_data(show_spinner="Carregando consumo diesel...", ttl=3600)
def diesel():
    return dl.load_diesel()


@st.cache_data(show_spinner="Carregando consumo veículos leves...", ttl=3600)
def etanol():
    return dl.load_etanol()


@st.cache_data(show_spinner="Carregando estoque...", ttl=3600)
def estoque():
    return dl.load_estoque()


@st.cache_data(show_spinner="Carregando NF diesel...", ttl=3600)
def nf_diesel():
    return dl.load_nf_diesel()


@st.cache_data(show_spinner="Carregando veículos leves...", ttl=3600)
def veiculos_leves():
    return dl.load_veiculos_leves()
