# ============================================
# pages/7_⚙️_Configuracion_ML.py
# ============================================
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))
from conexion_db import get_connection

st.set_page_config(page_title="Configuración ML", page_icon="⚙️", layout="wide")

if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Por favor inicie sesión primero")
    st.stop()

if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚫 Esta sección es solo para administradores")
    st.stop()

st.markdown("""
<div style="background: linear-gradient(90deg, #e84393 0%, #fd79a8 100%); 
            padding: 2rem; border-radius: 10px; margin-bottom: 2rem; color: white;">
    <h1>⚙️ Configuración de Modelos ML</h1>
    <p>Gestión y configuración de los modelos de Machine Learning</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔧 Parámetros", "📋 Estado de Modelos"])

with tab1:
    st.subheader("🔧 Configuración de Parámetros")
    
    st.info("Próximamente: Configuración de hiperparámetros y ajustes avanzados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Modelo de Demanda")
        train_split = st.slider("Train/Test Split (%)", 50, 90, 70)
        st.write(f"Entrenamiento: {train_split}% | Prueba: {100-train_split}%")
    
    with col2:
        st.markdown("### 🎯 Motor de Recomendaciones")
        peso_clic = st.number_input("Peso de clic", 1, 5, 1)
        peso_carrito = st.number_input("Peso añadir carrito", 1, 5, 2)
        peso_compra = st.number_input("Peso compra", 1, 5, 3)
    
    st.divider()
    
    st.markdown("### 🚨 Detección de Anomalías")
    umbral_cantidad = st.number_input("Umbral de cantidad sospechosa", 1, 10, 3)
    metodo_deteccion = st.selectbox("Método preferido", ["Auto", "IQR", "Media+Desviación"])
    
    if st.button("💾 Guardar Configuración", type="primary"):
        st.success("⚠️ Esta funcionalidad estará disponible en futuras versiones")

with tab2:
    st.subheader("📋 Estado de los Modelos")
    
    conn = get_connection()
    df_modelos = pd.read_sql_query("""
        SELECT 
            nombre_modelo,
            tipo,
            version,
            fecha_entrenamiento,
            accuracy,
            mae,
            estado
        FROM modelo_ml
        ORDER BY fecha_entrenamiento DESC
        LIMIT 20
    """, conn)
    conn.close()
    
    if not df_modelos.empty:
        st.dataframe(df_modelos, use_container_width=True)
        
        st.divider()
        st.subheader("📊 Resumen por Tipo de Modelo")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            demanda = len(df_modelos[df_modelos['tipo'] == 'prediccion_demanda'])
            st.metric("Modelos de Demanda", demanda)
        
        with col2:
            recom = len(df_modelos[df_modelos['tipo'] == 'recomendacion'])
            st.metric("Modelos de Recomendación", recom)
        
        with col3:
            anom = len(df_modelos[df_modelos['tipo'] == 'anomalias'])
            st.metric("Modelos de Anomalías", anom)
    else:
        st.info("No hay modelos entrenados aún")
