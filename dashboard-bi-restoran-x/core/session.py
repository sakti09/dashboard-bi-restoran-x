"""State bersama antar-halaman: dataset master disimpan di session_state sehingga
satu kali diunggah dapat dipakai semua halaman (sinkron lintas halaman)."""
import streamlit as st

_KEY = "master_df"
_SRC = "master_source"


def has_master() -> bool:
    return st.session_state.get(_KEY) is not None


def get_master():
    return st.session_state.get(_KEY)


def set_master(df, source: str):
    st.session_state[_KEY] = df
    st.session_state[_SRC] = source


def master_source() -> str:
    return st.session_state.get(_SRC, "")


def clear_master():
    st.session_state.pop(_KEY, None)
    st.session_state.pop(_SRC, None)
