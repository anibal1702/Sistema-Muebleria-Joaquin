# ============================================
# pages/6_📥_Carga_Datos.py
# ============================================
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))
from conexion_db import export_eventos_to_excel

st.set_page_config(page_title="Carga de Datos", page_icon="📥", layout="wide")

if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Por favor inicie sesión primero")
    st.stop()

if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚫 Esta sección es solo para administradores")
    st.stop()

st.markdown("""
<div style="background: linear-gradient(90deg, #00B894 0%, #55efc4 100%); 
            padding: 2rem; border-radius: 10px; margin-bottom: 2rem; color: white;">
    <h1>📥 Gestión de Datos</h1>
    <p>Importar y exportar datos del sistema</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📤 Exportar", "📥 Importar"])

with tab1:
    st.subheader("📤 Exportar Eventos a Excel")
    
    st.info("""
    Exporta todos los eventos de usuarios registrados en el sistema a un archivo Excel.
    Incluye: timestamp, usuario, tipo de evento, producto y detalles.
    """)
    
    if st.button("📊 Generar Excel", type="primary", use_container_width=True):
        with st.spinner("Generando archivo Excel..."):
            filename = export_eventos_to_excel()
            
            if filename:
                st.success(f"✅ Archivo generado: {filename}")
                
                try:
                    df = pd.read_excel(filename)
                    st.write("**Preview del archivo:**")
                    st.dataframe(df.head(20), use_container_width=True)
                    
                    with open(filename, 'rb') as f:
                        st.download_button(
                            label="⬇️ Descargar Excel",
                            data=f,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception as e:
                    st.warning(f"No se pudo leer el preview: {e}")
            else:
                st.warning("No hay eventos para exportar")

with tab2:
    st.subheader("📥 Importar Datos Históricos")
    
    st.info("""
    Carga archivos CSV o JSON con datos históricos de ventas para entrenar los modelos.
    """)
    
    uploaded_file = st.file_uploader(
        "Selecciona un archivo CSV o JSON",
        type=['csv', 'json']
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_json(uploaded_file)
            
            st.success(f"✅ Archivo cargado: {uploaded_file.name}")
            
            filas_original = len(df)
            df = df.dropna()
            df = df.drop_duplicates()
            filas_limpias = len(df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Filas originales", filas_original)
            with col2:
                st.metric("Filas después de limpieza", filas_limpias)
            
            st.write("**Preview:**")
            st.dataframe(df.head(20), use_container_width=True)
            
            if st.button("💾 Guardar datos limpios", type="primary"):
                output_file = "Datos_Historicos_Limpios.xlsx"
                df.to_excel(output_file, index=False)
                st.success(f"Guardado en: {output_file}")
        
        except Exception as e:
            st.error(f"Error al procesar archivo: {e}")

