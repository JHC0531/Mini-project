import streamlit as st

st.markdown("### Let's learn verbs with examples.")
st.caption("Since Apr 25, 2026")

# Image links
main_image_url = "https://github.com/jihyeon0531/WordApp/raw/main/images/image1.png"
qr_image_url = "https://github.com/jihyeon0531/WordApp/raw/main/images/appQR.png"

# Use columns to center images
col1, col2, col3 = st.columns([1, 2, 1])  # middle column bigger

with col1:
    st.image(main_image_url, width=500, caption="Welcome Image")  # Expand button appears
with col3:
    st.image(qr_image_url, width=50, caption="QR")  # Expand button appear
