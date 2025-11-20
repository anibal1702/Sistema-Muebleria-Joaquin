# ============================================
# pages/5_📡_Monitor_Eventos.py
# ============================================
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))
from conexion_db import get_connection

st.set_page_config(page_title="Monitor de Eventos", page_icon="📡", layout="wide")

if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Por favor inicie sesión primero")
    st.stop()

if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚫 Esta sección es solo para administradores")
    st.stop()

st.markdown("""
<div style="background: linear-gradient(90deg, #0984E3 0%, #74b9ff 100%); 
            padding: 2rem; border-radius: 10px; margin-bottom: 2rem; color: white;">
    <h1>📡 Monitor de Eventos en Tiempo Real</h1>
    <p>Visualiza las interacciones de usuarios en tiempo real</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def cargar_eventos():
    conn = get_connection()
    query = """
        SELECT 
            e.timestamp, 
            u.user AS usuario, 
            e.tipo_evento, 
            e.id_item, 
            e.detalles
        FROM evento_usuario e
        LEFT JOIN usuario u ON e.id_usuario = u.id_usuario
        ORDER BY e.timestamp DESC
        LIMIT 100
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

df = cargar_eventos()

if df.empty:
    st.info("No hay eventos registrados aún")
else:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Eventos", len(df))
    
    with col2:
        compras = len(df[df['tipo_evento'] == 'compra'])
        st.metric("Compras", compras)
    
    with col3:
        clics = len(df[df['tipo_evento'] == 'clic'])
        st.metric("Clics", clics)
    
    with col4:
        usuarios = df['usuario'].nunique()
        st.metric("Usuarios Activos", usuarios)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        tipos = ['Todos'] + df['tipo_evento'].unique().tolist()
        tipo_filtro = st.selectbox("Filtrar por tipo:", tipos)
    
    with col2:
        usuarios = ['Todos'] + df['usuario'].dropna().unique().tolist()
        usuario_filtro = st.selectbox("Filtrar por usuario:", usuarios)
    
    df_filtrado = df.copy()
    
    if tipo_filtro != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['tipo_evento'] == tipo_filtro]
    
    if usuario_filtro != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['usuario'] == usuario_filtro]
    
    st.write(f"**{len(df_filtrado)} eventos mostrados**")
    
    st.dataframe(df_filtrado, use_container_width=True, height=500)
    
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
        st.rerun()

