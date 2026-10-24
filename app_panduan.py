import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
from auth import check_login, apply_custom_css

check_login()
apply_custom_css()

st.title("📖 Panduan Trading")

# Ganti dengan nama file PDF Anda yang sebenarnya
file_path = "Trading_Saham_Syariah.pdf"

try:
    # pdf_viewer akan merender PDF dengan aman tanpa memicu blokir Chrome
    pdf_viewer(file_path, width=700)
except Exception as e:
    st.error("File PDF tidak ditemukan atau gagal dimuat. Pastikan file PDF sudah diunggah ke GitHub.")
