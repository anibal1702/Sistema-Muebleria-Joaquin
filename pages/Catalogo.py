import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from conexion_db import get_all_products, registrar_venta, get_recomendaciones_usuario
from logger import EventLogger

st.set_page_config(page_title="Catálogo", page_icon="🛒", layout="wide")

# Verificar login
if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Por favor inicie sesión primero")
    st.stop()

logger = EventLogger()
USER_ID = st.session_state.user_id

# CSS personalizado
st.markdown("""
<style>
    .product-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1E90FF;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .product-title {
        color: #1E90FF;
        font-size: 1.3em;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .product-price {
        color: #28A745;
        font-size: 1.5em;
        font-weight: bold;
    }
    .recom-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div style="background: linear-gradient(90deg, #1E90FF 0%, #00BFFF 100%); 
            padding: 2rem; border-radius: 10px; margin-bottom: 2rem; color: white;">
    <h1>🛒 Catálogo de Muebles de Dormitorio</h1>
    <p>Explora y compra tus muebles favoritos</p>
</div>
""", unsafe_allow_html=True)

# Obtener productos
PRODUCTS = get_all_products()

# Recomendaciones personalizadas
st.subheader("🎯 Recomendado para ti")
recomendaciones = get_recomendaciones_usuario(USER_ID, limite=3)

if recomendaciones:
    cols = st.columns(min(3, len(recomendaciones)))
    for idx, prod in enumerate(recomendaciones):
        with cols[idx]:
            st.markdown(f"""
            <div class="recom-card">
                <h4>{prod['nombre']}</h4>
                <p><b>{prod['categoria']}</b></p>
                <p style="font-size: 1.2em;">S/. {prod['precio']:.2f}</p>
                <p>Stock: {prod['stock']} unidades</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Ver producto", key=f"rec_{prod['id_producto']}"):
                logger.log_event(USER_ID, 'clic', prod['id_producto'])
                st.session_state.selected_product = prod['id_producto']
else:
    st.info("Explora productos y realiza compras para recibir recomendaciones personalizadas")

st.divider()

# Barra de búsqueda
col1, col2 = st.columns([3, 1])
with col1:
    search_term = st.text_input("🔍 Buscar productos", placeholder="Ej: cama, mesa, silla...")
with col2:
    st.write("")
    st.write("")
    if st.button("Buscar", use_container_width=True):
        if search_term:
            logger.log_event(USER_ID, 'busqueda', details=f"term:'{search_term}'")

# Filtrar productos
if search_term:
    filtered_products = [p for p in PRODUCTS if search_term.lower() in p['nombre'].lower() 
                         or search_term.lower() in p['categoria'].lower()]
else:
    filtered_products = PRODUCTS

st.write(f"**{len(filtered_products)} productos encontrados**")

# Mostrar productos
for producto in filtered_products:
    with st.container():
        st.markdown(f"""
        <div class="product-card">
            <div class="product-title">🛋 {producto['nombre']} | {producto['categoria']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**Descripción:** {producto['descripcion'][:150]}...")
            st.caption(f"💰 Precio: S/. {producto['precio']:.2f} | 📦 Stock: {producto['stock']} unidades")
        
        with col2:
            if st.button("👁️ Ver detalles", key=f"view_{producto['id_producto']}"):
                logger.log_event(USER_ID, 'clic', producto['id_producto'])
                
                with st.expander("📋 Información completa", expanded=True):
                    st.write(f"**{producto['nombre']}**")
                    st.write(f"**Descripción:** {producto['descripcion']}")
                    st.write(f"**Categoría:** {producto['categoria']}")
                    st.write(f"**Precio:** S/. {producto['precio']:.2f}")
                    st.write(f"**Stock disponible:** {producto['stock']} unidades")
        
        with col3:
            if st.button("🛒 Comprar", key=f"buy_{producto['id_producto']}", type="primary"):
                # Registrar evento de compra
                logger.log_event(USER_ID, 'compra', producto['id_producto'], 
                               details=f"price:{producto['precio']}")
                
                # Registrar venta
                try:
                    registrar_venta(
                        id_usuario=USER_ID,
                        id_producto=producto['id_producto'],
                        cantidad=1,
                        precio_unitario=producto['precio'],
                        publicidad=0.0
                    )
                    st.success(f"✅ ¡Has comprado {producto['nombre']}!")
                except Exception as e:
                    st.error(f"Error al registrar la venta: {e}")
        
        # Botones adicionales en una nueva fila
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col2:
            if st.button("➕ Añadir al carrito", key=f"cart_{producto['id_producto']}"):
                logger.log_event(USER_ID, 'add_to_cart', producto['id_producto'])
                st.info(f"📦 {producto['nombre']} añadido al carrito")
        
        with col3:
            if st.button("⭐ Calificar (5★)", key=f"rate_{producto['id_producto']}"):
                logger.log_event(USER_ID, 'rating', producto['id_producto'], details="rating:5")
                st.success("¡Gracias por tu calificación!")

# Sidebar con información
with st.sidebar:
    st.markdown(f"""
    ### 👤 Usuario: {st.session_state.user_name}
    **Rol:** {st.session_state.user_role}
    """)
    
    st.divider()
    
    st.markdown("""
    ### 📊 Estadísticas
    """)
    st.metric("Productos en catálogo", len(PRODUCTS))
    st.metric("Productos en tu búsqueda", len(filtered_products))
    
    st.divider()
    
    st.markdown("""
    ### 💡 Tip
    Interactúa con los productos para recibir recomendaciones personalizadas basadas en tus preferencias.
    """)
