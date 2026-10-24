"""Panduan Trading PDF viewer."""

import base64
from pathlib import Path

import streamlit as st

from auth import check_login, apply_custom_css

check_login()
apply_custom_css()

st.title("📖 Panduan Trading")

file_path = Path(__file__).with_name("Trading_Saham_Syariah.pdf")

try:
    with file_path.open("rb") as pdf_file:
        base64_pdf = base64.b64encode(pdf_file.read()).decode("utf-8")

    pdf_display = (
        f'<iframe src="data:application/pdf;base64,{base64_pdf}" '
        'width="100%" height="800" type="application/pdf"></iframe>'
    )
    st.markdown(pdf_display, unsafe_allow_html=True)
except FileNotFoundError:
    st.error(
        "File PDF tidak ditemukan. Pastikan Trading_Saham_Syariah.pdf "
        "tersedia di folder aplikasi."
    )
