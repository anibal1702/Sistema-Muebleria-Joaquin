import streamlit as st
import sys
from pathlib import Path
from modules.navegacion import mostrar_menu_lateral

# Agregar el directorio modules al path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from conexion_db import verify_user, create_user

# Configuración de la página
st.set_page_config(
    page_title="Creaciones Joaquín - Sistema IA",
    page_icon="🛋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1E90FF 0%, #00BFFF 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .stButton>button {
        width: 100%;
        background-color: #28A745;
        color: white;
        border-radius: 5px;
        padding: 0.5rem;
        font-weight: bold;
    }
    .logout-button>button {
        background-color: #E63946;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

def login_page():
    """Página de login"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="main-header">
            <h1 style="text-align: center;">🛋 Creaciones Joaquín</h1>
            <p style="text-align: center;">Sistema Inteligente de Gestión</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Usuario", placeholder="Ingrese su usuario")
                password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
                submit = st.form_submit_button("Ingresar", use_container_width=True)
                
                if submit:
                    if username and password:
                        result = verify_user(username, password)
                        if result:
                            st.session_state.logged_in = True
                            st.session_state.user_id = result[0]
                            st.session_state.user_name = result[1]
                            st.session_state.user_role = result[2]
                            st.success(f"¡Bienvenido {result[1]}!")
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos")
                    else:
                        st.warning("Por favor complete todos los campos")
        
        with tab2:
            with st.form("register_form"):
                name = st.text_input("Nombre completo")
                new_user = st.text_input("Nombre de usuario")
                email = st.text_input("Correo electrónico")
                new_pass = st.text_input("Contraseña", type="password")
                register = st.form_submit_button("Crear cuenta", use_container_width=True)
                
                if register:
                    if name and new_user and email and new_pass:
                        if create_user(name, new_user, email, new_pass):
                            st.success("¡Cuenta creada exitosamente! Ahora puede iniciar sesión.")
                        else:
                            st.error("El usuario o correo ya existe")
                    else:
                        st.warning("Por favor complete todos los campos")

def main_app():
    """Aplicación principal después del login"""
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        ### 👋 Hola, {st.session_state.user_name}
        **Rol:** {st.session_state.user_role.capitalize() if st.session_state.user_role else 'Cliente'}
        """)
        st.divider()
        mostrar_menu_lateral()
        st.divider()
        
        if st.button("🚪 Cerrar sesión", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Contenido principal
    st.markdown("""
    <div class="main-header">
        <h1>🛋 Mueblería Joaquín</h1>
        <p>Sistema de gestión inteligente con Machine Learning</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Menú según el rol
    role = (st.session_state.user_role or "").lower()
    
    if role == "cliente":
        st.info("👈 Usa el menú lateral para navegar al **Catálogo de Productos**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🛒 Catálogo</h3>
                <p>Explora el catálogo y realiza compras.</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>🎯 Recomendaciones</h3>
                <p>Productos personalizados para ti</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>⭐ Favoritos</h3>
                <p>Tus productos guardados</p>
            </div>
            """, unsafe_allow_html=True)
    
    elif role == "admin":
        st.info("👈 Usa el menú lateral para acceder a todas las funcionalidades del sistema")
        
        st.subheader("📊 Panel de Control Administrativo")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h4>📥 Gestión de Datos</h4>
                <ul style="font-size: 0.9em;">
                    <li>Carga de datos históricos</li>
                    <li>Monitor de eventos</li>
                    <li>Exportar a Excel</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h4>🤖 Machine Learning</h4>
                <ul style="font-size: 0.9em;">
                    <li>Predicción de demanda</li>
                    <li>Recomendaciones</li>
                    <li>Detección de anomalías</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h4>📊 Dashboards</h4>
                <ul style="font-size: 0.9em;">
                    <li>Dashboard de demanda</li>
                    <li>Dashboard de recomendaciones</li>
                    <li>Centro de alertas</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h4>⚙️ Configuración</h4>
                <ul style="font-size: 0.9em;">
                    <li>Re-entrenamiento automático</li>
                    <li>Parámetros de modelos</li>
                    <li>Monitoreo de sistema</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

# Flujo principal
if st.session_state.logged_in:
    main_app()
else:
    login_page()

