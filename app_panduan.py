"""Panduan Trading PDF viewer."""

from pathlib import Path

import streamlit as st

from auth import apply_custom_css, check_login

check_login()
apply_custom_css()

st.title("📖 Panduan Trading")

file_path = Path(__file__).resolve().with_name("Trading_Saham_Syariah.pdf")

try:
    st.pdf(
        file_path,
        height=800,
        alt="Panduan trading saham syariah",
    )
except FileNotFoundError:
    st.error(
        "File PDF tidak ditemukan. Pastikan Trading_Saham_Syariah.pdf "
        "sudah disertakan di repository dengan nama dan kapitalisasi yang sama."
    )
except OSError as exc:
    st.error(f"File PDF tidak dapat dibaca: {exc}")

if file_path.is_file():
    try:
        st.download_button(
            "⬇️ Unduh Panduan Trading",
            data=file_path.read_bytes(),
            file_name=file_path.name,
            mime="application/pdf",
            use_container_width=True,
        )
    except OSError as exc:
        st.error(f"Tidak dapat menyiapkan unduhan PDF: {exc}")
