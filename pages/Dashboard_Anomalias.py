import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from anomalia import detectar_anomalias_en_ventas
from conexion_db import get_connection

st.set_page_config(page_title="Centro de Alertas", page_icon="🚨", layout="wide")

# Verificar login y rol
if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Por favor inicie sesión primero")
    st.stop()

if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚫 Esta sección es solo para administradores")
    st.stop()

# Header
st.markdown("""
<div style="background: linear-gradient(90deg, #E74C3C 0%, #C0392B 100%); 
            padding: 2rem; border-radius: 10px; margin-bottom: 2rem; color: white;">
    <h1>🚨 Centro de Alertas y Monitoreo</h1>
    <p>Detección de anomalías en ventas y comportamiento de usuarios</p>
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["🔍 Detección", "📊 Alertas Activas", "📋 Historial"])

with tab1:
    st.subheader("🔍 Detectar Anomalías")
    
    st.info("""
    **¿Qué detecta este sistema?**
    - Ventas con montos fuera del rango normal (usando IQR o desviación estándar)
    - Cantidades de compra excesivas (más de 3 unidades)
    - Usuarios que compran más de 3 veces el mismo producto
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Ejecutar Detección", type="primary", use_container_width=True):
            with st.spinner("Analizando ventas..."):
                try:
                    resultado = detectar_anomalias_en_ventas()
                    
                    # Guardar en session_state
                    st.session_state.anomalias_resultado = resultado
                    st.session_state.anomalias_timestamp = datetime.now()
                    
                    st.success(f"✅ Análisis completado: {resultado['mensaje']}")
                    
                except Exception as e:
                    st.error(f"❌ Error en detección: {e}")
    
    with col2:
        st.markdown("""
        ### 📊 Métodos de Detección
        
        **IQR (Interquartile Range):**
        - Para datasets con 5+ registros
        - Detecta outliers usando boxplot
        
        **Media + Desviación:**
        - Para datasets pequeños
        - Umbral: ±2 desviaciones estándar
        """)
    
    # Mostrar resultados si existen
    if 'anomalias_resultado' in st.session_state:
        st.divider()
        resultado = st.session_state.anomalias_resultado
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            color = "🔴" if resultado['anomalias'] > 0 else "🟢"
            st.metric("Estado del Sistema", f"{color} {'Alertas' if resultado['anomalias'] > 0 else 'Normal'}")
        
        with col2:
            st.metric("Alertas Detectadas", resultado['anomalias'])
        
        with col3:
            st.metric("Ventas Analizadas", resultado['total_analizadas'])
        
        with col4:
            st.metric("ID Modelo", resultado['modelo'] or "N/A")

with tab2:
    st.subheader("📊 Alertas Activas")
    
    if 'anomalias_resultado' in st.session_state:
        resultado = st.session_state.anomalias_resultado
        detalles = resultado.get('detalles', [])
        
        if not detalles:
            st.success("✅ No hay alertas pendientes. El sistema opera normalmente.")
        else:
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                nivel_filtro = st.selectbox(
                    "Filtrar por nivel:",
                    ["Todos", "alto", "medio"]
                )
            
            # Aplicar filtro
            if nivel_filtro != "Todos":
                detalles_filtrados = [d for d in detalles if d['nivel'] == nivel_filtro]
            else:
                detalles_filtrados = detalles
            
            st.write(f"**{len(detalles_filtrados)} alertas mostradas**")
            
            # Mostrar tabla
            df_alertas = pd.DataFrame(detalles_filtrados)
            
            # Estilizar según nivel
            def color_nivel(val):
                if val == 'alto':
                    return 'background-color: #FFCCCC'
                elif val == 'medio':
                    return 'background-color: #FFF4CC'
                return ''
            
            if not df_alertas.empty:
                styled_df = df_alertas.style.applymap(
                    color_nivel, 
                    subset=['nivel'] if 'nivel' in df_alertas.columns else None
                )
                st.dataframe(styled_df, use_container_width=True)
                
                # Gráfico de distribución por nivel
                if 'nivel' in df_alertas.columns:
                    st.subheader("📊 Distribución por Nivel de Severidad")
                    nivel_counts = df_alertas['nivel'].value_counts()
                    fig = px.pie(
                        values=nivel_counts.values,
                        names=nivel_counts.index,
                        color=nivel_counts.index,
                        color_discrete_map={'alto': '#E74C3C', 'medio': '#F39C12'},
                        hole=0.4
                    )
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Ejecuta primero la detección en la pestaña 'Detección'")

with tab3:
    st.subheader("📋 Historial de Anomalías")
    
    @st.cache_data(ttl=300)
    def cargar_historial():
        conn = get_connection()
        query = """
            SELECT 
                a.id_venta,
                a.nivel,
                a.descripcion,
                a.valor_detectado,
                a.fecha_detectada
            FROM anomalia a
            ORDER BY a.fecha_detectada DESC
            LIMIT 100
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    df_historial = cargar_historial()
    
    if not df_historial.empty:
        st.write(f"**{len(df_historial)} registros históricos**")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            nivel_hist = st.multiselect(
                "Filtrar por nivel:",
                options=df_historial['nivel'].unique(),
                default=df_historial['nivel'].unique()
            )
        
        df_filtrado = df_historial[df_historial['nivel'].isin(nivel_hist)]
        
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Gráfico de tendencia
        st.subheader("📈 Tendencia de Anomalías")
        df_filtrado['fecha'] = pd.to_datetime(df_filtrado['fecha_detectada']).dt.date
        anomalias_por_dia = df_filtrado.groupby('fecha').size().reset_index(name='cantidad')
        
        fig = px.line(
            anomalias_por_dia,
            x='fecha',
            y='cantidad',
            markers=True,
            labels={'fecha': 'Fecha', 'cantidad': 'Número de Anomalías'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("No hay registros históricos de anomalías")

# Sidebar
with st.sidebar:
    st.markdown("### ℹ️ Configuración")
    
    st.markdown("""
    **Criterios de Detección:**
    
    - **IQR:** Q1 - 1.5×IQR, Q3 + 1.5×IQR
    - **Cantidad alta:** > 3 unidades
    - **Compras repetidas:** > 3 veces mismo producto
    """)
    
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
