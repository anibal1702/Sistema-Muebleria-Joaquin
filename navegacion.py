import streamlit as st

def mostrar_menu_lateral():
    # Si no hay rol en la sesión, no mostramos nada
    if 'rol' not in st.session_state:
        return

    # Recuperamos los datos de la sesión
    rol_usuario = st.session_state['rol']
    nombre_usuario = st.session_state.get('nombre', 'Usuario')

    with st.sidebar:
        # ---------------------------------------------------
        # 1. TU SECCIÓN DE USUARIO (Lo que pediste)
        # ---------------------------------------------------
        st.write(f"👋 Hola, **{nombre_usuario}**")
        st.caption(f"Rol: {rol_usuario}")
        st.divider() # Una línea para separar info del menú

        # ---------------------------------------------------
        # 2. SECCIÓN DE NAVEGACIÓN (Depende del rol)
        # ---------------------------------------------------
        
        # --- SI ES CLIENTE ---
        if rol_usuario == "Cliente":
            st.header("Tienda")
            # Ajusta el nombre del archivo si tiene espacios o guiones
            st.page_link("pages/Catalogo.py", label="Ir al Catálogo", icon="🛒")

        # --- SI ES ADMIN ---
        elif rol_usuario == "Admin":
            st.header("Navegación")
            
            # Inicio
            st.page_link("app.py", label="Inicio", icon="🏠")
            
            # Sección operativa
            st.subheader("Operativo")
            st.page_link("pages/Catalogo.py", label="Catálogo", icon="🛒")
            st.page_link("pages/Carga_Datos.py", label="Carga de Datos", icon="📤")
            
            # Sección analítica
            st.subheader("Dashboards")
            st.page_link("pages/Dashboard_Demanda.py", label="Demanda", icon="📊")
            st.page_link("pages/Dashboard_Recomendaciones.py", label="Recomendaciones", icon="🎯")
            st.page_link("pages/Dashboard_Anomalias.py", label="Anomalías", icon="🚨")
            st.page_link("pages/Monitor_Eventos.py", label="Monitor de Eventos", icon="👀")
            
            # Sección técnica
            st.subheader("Configuración")
            st.page_link("pages/Configuracion_ML.py", label="Configuración ML", icon="⚙️")

        # ---------------------------------------------------
        # 3. TU BOTÓN DE CERRAR SESIÓN
        # ---------------------------------------------------
        st.divider() # Línea separadora final
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.rerun()