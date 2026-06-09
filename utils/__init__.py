def get_lang():
    import streamlit as st
    return st.session_state.get("lang", "zh")

def tr_factory(zh_text, en_text):
    return zh_text if get_lang() == "zh" else en_text
