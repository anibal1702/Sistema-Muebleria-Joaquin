import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from conexion_db import get_connection
from modelo_demanda import entrenar_modelo_demanda

st.set_page_config(page_title="Dashboard Demanda", page_icon="📊", layout="wide")

# Verificar login y rol admin
if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Por favor inicie sesión primero")
    st.stop()

if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚫 Esta sección es solo para administradores")
    st.stop()

# Header
st.markdown("""
<div style="background: linear-gradient(90deg, #1E90FF 0%, #00BFFF 100%); 
            padding: 2rem; border-radius: 10px; margin-bottom: 2rem; color: white;">
    <h1>📊 Dashboard de Predicción de Demanda</h1>
    <p>Análisis y pronóstico de ventas por producto</p>
</div>
""", unsafe_allow_html=True)

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📈 Visualización", "🤖 Entrenamiento", "📋 Datos"])

# Cargar datos desde BD
@st.cache_data(ttl=300)
def cargar_datos():
    conn = get_connection()
    
    # Último modelo
    df_modelo = pd.read_sql_query("""
        SELECT *
        FROM modelo_ml
        WHERE tipo = 'prediccion_demanda'
        ORDER BY datetime(fecha_entrenamiento) DESC
        LIMIT 1
    """, conn)
    
    if df_modelo.empty:
        conn.close()
        return None, None, None
    
    id_modelo_actual = int(df_modelo.iloc[0]["id_modelo"])
    
    # Predicciones
    df_pred = pd.read_sql_query(f"""
        SELECT 
            d.id_producto,
            p.nombre,
            d.demanda_esperada
        FROM prediccion_demanda d
        LEFT JOIN producto p ON d.id_producto = p.id_producto
        WHERE d.id_modelo = {id_modelo_actual}
    """, conn)
    
    # Ventas históricas
    df_ventas = pd.read_sql_query("""
        SELECT id_producto, COUNT(*) AS ventas
        FROM venta
        GROUP BY id_producto
    """, conn)
    
    conn.close()
    
    return df_modelo, df_pred, df_ventas

df_modelo, df_pred, df_ventas = cargar_datos()

with tab1:
    if df_pred is None or df_pred.empty:
        st.warning("⚠️ No hay datos de predicción. Entrena el modelo primero en la pestaña 'Entrenamiento'")
    else:
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Demanda Total Proyectada", f"{int(df_pred['demanda_esperada'].sum())} unidades")
        
        with col2:
            st.metric("Productos Analizados", len(df_pred))
        
        with col3:
            mae = df_modelo.iloc[0]['mae'] if not df_modelo.empty else 0
            st.metric("Error MAE", f"{mae:.2f}")
        
        with col4:
            fecha = df_modelo.iloc[0]['fecha_entrenamiento'] if not df_modelo.empty else "N/A"
            st.metric("Último Entrenamiento", fecha[:10])
        
        st.divider()
        
        # Filtro por producto
        col1, col2 = st.columns([3, 1])
        with col1:
            productos = ["Todos"] + sorted(df_pred["id_producto"].unique().tolist())
            filtro = st.selectbox("Filtrar por producto:", productos)
        
        # Filtrar datos
        if filtro != "Todos":
            df_p = df_pred[df_pred["id_producto"] == filtro]
            df_v = df_ventas[df_ventas["id_producto"] == filtro] if not df_ventas.empty else pd.DataFrame()
        else:
            df_p = df_pred
            df_v = df_ventas if not df_ventas.empty else pd.DataFrame()
        
        # Gráficos lado a lado
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📉 Ventas Históricas")
            if not df_v.empty:
                fig1 = px.bar(df_v, x='id_producto', y='ventas',
                             labels={'id_producto': 'Producto', 'ventas': 'Ventas'},
                             color_discrete_sequence=['#00B894'])
                fig1.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No hay datos de ventas históricas")
        
        with col2:
            st.subheader("📈 Demanda Proyectada")
            if not df_p.empty:
                fig2 = px.bar(df_p, x='id_producto', y='demanda_esperada',
                             labels={'id_producto': 'Producto', 'demanda_esperada': 'Demanda'},
                             color_discrete_sequence=['#0984E3'])
                fig2.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No hay predicciones disponibles")
        
        # Comparación
        if not df_v.empty and not df_p.empty:
            st.subheader("⚖️ Comparación: Ventas vs Predicción")
            
            df_comp = df_p.merge(df_v, on='id_producto', how='left')
            df_comp['ventas'] = df_comp['ventas'].fillna(0)
            
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(name='Ventas Reales', x=df_comp['id_producto'], 
                                  y=df_comp['ventas'], marker_color='#00B894'))
            fig3.add_trace(go.Bar(name='Demanda Predicha', x=df_comp['id_producto'], 
                                  y=df_comp['demanda_esperada'], marker_color='#0984E3'))
            
            fig3.update_layout(barmode='group', height=400)
            st.plotly_chart(fig3, use_container_width=True)

with tab2:
    st.subheader("🤖 Entrenar Modelo de Predicción de Demanda")
    
    st.info("""
    **¿Qué hace este modelo?**
    - Analiza las ventas históricas de cada producto
    - Genera predicciones de demanda futura usando regresión lineal
    - Calcula métricas de error (MAE) para evaluar la precisión
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Entrenar Modelo", type="primary", use_container_width=True):
            with st.spinner("Entrenando modelo..."):
                try:
                    resultado = entrenar_modelo_demanda()
                    
                    st.success("✅ Modelo entrenado exitosamente!")
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("MAE (Train)", f"{resultado['mae_train']:.3f}")
                    with col_b:
                        st.metric("MAE (Test)", f"{resultado['mae_test']:.3f}")
                    with col_c:
                        st.metric("Productos", len(resultado['resumen']))
                    
                    # Mostrar resumen
                    st.subheader("📋 Resumen de Predicciones")
                    df_resumen = pd.DataFrame(resultado['resumen'])
                    st.dataframe(df_resumen, use_container_width=True)
                    
                    # Limpiar cache para recargar datos
                    st.cache_data.clear()
                    
                except Exception as e:
                    st.error(f"❌ Error al entrenar: {e}")
    
    with col2:
        st.markdown("""
        ### 📊 Métricas
        
        **MAE (Mean Absolute Error):**
        - Promedio de errores absolutos
        - Valores más bajos = mejor predicción
        - Se calcula en conjunto Train y Test
        
        **Train/Test Split:**
        - 70% datos de entrenamiento
        - 30% datos de prueba
        """)

with tab3:
    st.subheader("📋 Datos del Modelo Actual")
    
    if df_pred is not None and not df_pred.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Predicciones por Producto:**")
            st.dataframe(df_pred, use_container_width=True)
        
        with col2:
            if not df_ventas.empty:
                st.write("**Ventas Históricas:**")
                st.dataframe(df_ventas, use_container_width=True)
            else:
                st.info("No hay datos de ventas históricas")
        
        # Botón de exportación
        if st.button("📥 Exportar datos a CSV"):
            csv = df_pred.to_csv(index=False)
            st.download_button(
                label="⬇️ Descargar CSV",
                data=csv,
                file_name=f"predicciones_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("No hay datos para mostrar")

# Sidebar
with st.sidebar:
    st.markdown("### ℹ️ Información")
    st.markdown("""
    Este dashboard permite:
    - Visualizar predicciones de demanda
    - Entrenar modelos de ML
    - Comparar ventas reales vs predichas
    - Exportar datos
    """)
