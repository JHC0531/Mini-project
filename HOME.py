import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Verb Pattern Learning App",
    page_icon="🐥",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
main_image_path = BASE_DIR / "images" / "main_chick.png"
qr_image_path = BASE_DIR / "images" / "app-qr.png"

st.title("Verb Pattern Learning App")
st.caption("Made by 조재민, 최지현")

st.image(str(main_image_path), use_container_width=True)

st.markdown("---")

col1, col2 = st.columns([5, 1])

with col2:
    st.caption("Scan here")
    st.image(str(qr_image_path), width=120)
