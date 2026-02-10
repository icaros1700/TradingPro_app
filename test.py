import streamlit as st

st.title("🧪 Test de Animaciones")

# 1. Verificar si la librería carga
try:
    from streamlit_extras.let_it_rain import rain
    st.success("✅ La librería 'streamlit-extras' está INSTALADA y DETECTADA.")
except ImportError:
    st.error("❌ La librería NO se encuentra. Ejecuta: pip install streamlit-extras")
    st.stop()

# 2. Botones para probar
col1, col2 = st.columns(2)

with col1:
    if st.button("💸 Probar Lluvia de Dinero"):
        rain(
            emoji="💸",
            font_size=54,
            falling_speed=2,
            animation_length="3s",
            emoji_count=100
        )

with col2:
    if st.button("💀 Probar Lluvia de Calaveras"):
        rain(
            emoji="💀",
            font_size=54,
            falling_speed=1,
            animation_length="2s",
            emoji_count=50
        )