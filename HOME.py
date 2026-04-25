import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Verb Pattern Learning App",
    page_icon="🐥",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
image_path = BASE_DIR / "images" / "main_chick.png"

st.title("Verb Pattern Learning App")
st.image(str(image_path), use_container_width=True)

st.markdown("## I will memorize all the verbs!")
