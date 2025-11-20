import streamlit as st

def mostrar_menu_lateral():
    """
    Esta función dibuja el menú lateral.
    Debe importarse y llamarse en CADA página de la app.
    """
    # 1. Recuperamos variables (con tus nombres correctos)
    rol = st.session_state.get('user_role', '')
    nombre = st.session_state.get('user_name', 'Usuario')

    # Si no hay rol, no dibujamos nada (probablemente no se ha logueado)
    if not rol:
        return

    with st.sidebar:

        # --- PARTE CENTRAL: NAVEGACIÓN ---
        
        # Normalizamos para evitar errores de mayúsculas
        rol_seguro = str(rol).strip().upper()

        # CLIENTE
        if rol_seguro == "CLIENTE":
            st.page_link("pages/Catalogo.py", label="Abrir tienda virtual", icon="🛒")
        
        # ADMIN (Usamos 'in' por si dice 'Super Admin' o algo así)
        elif "ADMIN" in rol_seguro:
            st.page_link("app.py", label="Inicio", icon="🏠")
            st.page_link("pages/Catalogo.py", label="Tienda virtual", icon="🛒")
            st.page_link("pages/Dashboard_Demanda.py", label="Dashborad demanda", icon="📊")
            st.page_link("pages/Dashboard_Recomendaciones.py", label="Recomendaciones", icon="🎯")
            st.page_link("pages/Dashboard_Anomalias.py", label="Dashboard anomalías", icon="🚨")
            st.page_link("pages/Monitor_Eventos.py", label="Monitor de eventos", icon="👀")
            st.page_link("pages/Carga_Datos.py", label="Carga Datos", icon="📤")
            st.page_link("pages/Configuracion_ML.py", label="Configuración ML", icon="🤖")
        
        else:
            st.warning(f"Rol '{rol}' sin accesos configurados.")














