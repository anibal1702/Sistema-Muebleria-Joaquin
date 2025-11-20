import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from conexion_db import get_connection
from motor_recomendacion import entrenar_motor_recomendacion

st.set_page_config(page_title="Dashboard Recomendaciones", page_icon="🎯", layout="wide")

# Verificar login y rol
if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Por favor inicie sesión primero")
    st.stop()

if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚫 Esta sección es solo para administradores")
    st.stop()

# Header
st.markdown("""
<div style="background: linear-gradient(90deg, #9b59b6 0%, #8e44ad 100%); 
            padding: 2rem; border-radius: 10px; margin-bottom: 2rem; color: white;">
    <h1>🎯 Dashboard de Recomendaciones</h1>
    <p>Motor de recomendaciones personalizadas por usuario</p>
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Visualización", "🤖 Entrenamiento", "📋 Top Productos"])

@st.cache_data(ttl=300)
def cargar_datos_recomendaciones():
    conn = get_connection()
    
    # Interacciones por producto
    query_interacciones = """
        WITH interacciones AS (
            SELECT 
                e.id_item AS id_producto,
                SUM(CASE WHEN e.tipo_evento = 'clic' THEN 1 ELSE 0 END) AS clics,
                SUM(CASE WHEN e.tipo_evento = 'add_to_cart' THEN 1 ELSE 0 END) AS carrito,
                SUM(CASE WHEN e.tipo_evento = 'compra' THEN 1 ELSE 0 END) AS compras,
                COUNT(*) AS total_interacciones
            FROM evento_usuario e
            GROUP BY e.id_item
        )
        SELECT
            p.id_producto,
            p.nombre,
            p.categoria,
            COALESCE(i.clics, 0) AS clics,
            COALESCE(i.carrito, 0) AS carrito,
            COALESCE(i.compras, 0) AS compras,
            COALESCE(i.total_interacciones, 0) AS total_interacciones
        FROM producto p
        LEFT JOIN interacciones i ON p.id_producto = i.id_producto
        ORDER BY total_interacciones DESC
    """
    
    df_productos = pd.read_sql_query(query_interacciones, conn)
    
    # Top recomendaciones
    query_recom = """
        SELECT 
            u.user AS usuario,
            p.nombre AS producto,
            r.puntaje_recomendacion
        FROM recomendacion r
        LEFT JOIN usuario u ON r.id_usuario = u.id_usuario
        LEFT JOIN producto p ON r.id_producto = p.id_producto
        ORDER BY r.puntaje_recomendacion DESC
        LIMIT 50
    """
    
    df_recom = pd.read_sql_query(query_recom, conn)
    
    # Usuarios activos
    query_usuarios = """
        SELECT COUNT(DISTINCT id_usuario) AS activos 
        FROM evento_usuario
    """
    
    df_usuarios = pd.read_sql_query(query_usuarios, conn)
    
    conn.close()
    
    return df_productos, df_recom, df_usuarios

df_productos, df_recom, df_usuarios = cargar_datos_recomendaciones()

with tab1:
    if df_productos.empty:
        st.warning("⚠️ No hay datos de interacciones disponibles")
    else:
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Interacciones", df_productos['total_interacciones'].sum())
        
        with col2:
            producto_top = df_productos.iloc[0]['nombre'] if not df_productos.empty else "N/A"
            st.metric("Producto Top", producto_top[:20] + "...")
        
        with col3:
            usuarios_activos = int(df_usuarios.iloc[0]['activos']) if not df_usuarios.empty else 0
            st.metric("Usuarios Activos", usuarios_activos)
        
        with col4:
            st.metric("Productos Monitoreados", len(df_productos))
        
        st.divider()
        
        # Gráfico: Top 10 productos más interactuados
        st.subheader("🔥 Top 10 Productos Más Interactuados")
        
        top10 = df_productos.head(10)
        
        fig = px.bar(
            top10,
            x='id_producto',
            y='total_interacciones',
            color='total_interacciones',
            labels={'id_producto': 'Producto', 'total_interacciones': 'Interacciones'},
            color_continuous_scale='Viridis'
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Desglose por tipo de interacción
        st.subheader("📊 Desglose por Tipo de Interacción (Top 10)")
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Clics', x=top10['id_producto'], y=top10['clics'], 
                              marker_color='#3498db'))
        fig2.add_trace(go.Bar(name='Carrito', x=top10['id_producto'], y=top10['carrito'], 
                              marker_color='#f39c12'))
        fig2.add_trace(go.Bar(name='Compras', x=top10['id_producto'], y=top10['compras'], 
                              marker_color='#2ecc71'))
        
        fig2.update_layout(barmode='group', height=400)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Tabla detallada
        st.subheader("📋 Detalle de Interacciones por Producto")
        st.dataframe(df_productos, use_container_width=True)

with tab2:
    st.subheader("🤖 Entrenar Motor de Recomendaciones")
    
    st.info("""
    **¿Cómo funciona?**
    - Analiza las interacciones de cada usuario (clics, carrito, compras)
    - Asigna puntajes: Clic = 1, Carrito = 2, Compra = 3
    - Normaliza los puntajes entre 0 y 1 para cada usuario
    - Genera recomendaciones personalizadas
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Entrenar Motor", type="primary", use_container_width=True):
            with st.spinner("Entrenando motor de recomendaciones..."):
                try:
                    resultado = entrenar_motor_recomendacion()
                    
                    st.success("✅ Motor entrenado exitosamente!")
                    
                    # Métricas del entrenamiento
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.metric("Usuarios", resultado['total_usuarios'])
                    
                    with col_b:
                        st.metric("Recomendaciones", resultado['total_recomendaciones'])
                    
                    with col_c:
                        st.metric("Promedio/Usuario", resultado['promedio_recs_por_usuario'])
                    
                    # Info del producto top
                    st.info(f"""
                    **🔥 Producto más popular:**
                    - {resultado['top_producto_nombre']}
                    - {resultado['top_producto_total']} interacciones
                    """)
                    
                    # Limpiar cache
                    st.cache_data.clear()
                    
                except ValueError as e:
                    st.error(f"❌ Error: {e}")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")
    
    with col2:
        st.markdown("""
        ### 📊 Sistema de Ponderación
        
        **Puntajes por evento:**
        - 👁️ Clic: 1 punto
        - 🛒 Añadir al carrito: 2 puntos
        - ✅ Compra: 3 puntos
        
        **Normalización:**
        Los puntajes se escalan de 0 a 1 para cada usuario, donde 1 representa máximo interés.
        """)
    
    # Mostrar recomendaciones actuales
    if not df_recom.empty:
        st.divider()
        st.subheader("🎯 Top 20 Recomendaciones Actuales")
        st.dataframe(df_recom.head(20), use_container_width=True)

with tab3:
    st.subheader("🏆 Productos Más Vendidos y Populares")
    
    if not df_productos.empty:
        # Top por compras
        st.write("**🛒 Top 5 Más Comprados:**")
        top_compras = df_productos.nlargest(5, 'compras')[['nombre', 'compras', 'categoria']]
        
        for idx, row in top_compras.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{row['nombre']}**")
            with col2:
                st.metric("Compras", int(row['compras']))
            with col3:
                st.caption(row['categoria'])
        
        st.divider()
        
        # Top por clics
        st.write("**👁️ Top 5 Más Vistos:**")
        top_clics = df_productos.nlargest(5, 'clics')[['nombre', 'clics', 'categoria']]
        
        for idx, row in top_clics.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{row['nombre']}**")
            with col2:
                st.metric("Clics", int(row['clics']))
            with col3:
                st.caption(row['categoria'])
        
        # Gráfico de dispersión: Clics vs Compras
        st.divider()
        st.subheader("📊 Relación: Clics vs Compras")
        
        fig = px.scatter(
            df_productos,
            x='clics',
            y='compras',
            size='total_interacciones',
            hover_data=['nombre', 'categoria'],
            labels={'clics': 'Clics', 'compras': 'Compras'},
            color='categoria'
        )
        st.plotly_chart(fig, use_container_width=True)

# Sidebar
with st.sidebar:
    st.markdown("### ℹ️ Información")
    st.markdown("""
    Este dashboard permite:
    - Analizar interacciones por producto
    - Entrenar el motor de recomendaciones
    - Ver productos más populares
    - Identificar patrones de comportamiento
    """)
    
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
