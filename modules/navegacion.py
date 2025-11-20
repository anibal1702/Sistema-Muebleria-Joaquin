import streamlit as st
import os

def mostrar_menu_lateral():
    # 1. Verificamos si hay rol
    if 'rol' not in st.session_state:
        return

    rol = st.session_state['rol']
    
    # --- ZONA DE INFORMACIÓN (Siempre visible) ---
    with st.sidebar:
        st.write(f"👤 Usuario: **{st.session_state.get('nombre', 'User')}**")
        
        # --- DIAGNÓSTICO (Esto nos dirá la verdad) ---
        st.divider()
        st.warning(f"🕵️ DIAGNÓSTICO: El rol exacto es: '{rol}'")
        
        # Verificamos si el archivo existe realmente
        archivo_demo = "pages/Catalogo.py"
        if os.path.exists(archivo_demo):
            st.success(f"✅ Archivo {archivo_demo} encontrado.")
        else:
            st.error(f"❌ NO SE ENCUENTRA: {archivo_demo}")
        st.divider()
        # ---------------------------------------------

        st.header("Menú de Navegación")

        # 2. PRUEBA DE FUEGO: Botón sin condiciones (Debe salir SÍ o SÍ)
        st.page_link("pages/Catalogo.py", label="Prueba Directa Catalogo", icon="🔥")

        # 3. LÓGICA CONDICIONAL
        # Usamos .strip() para quitar espacios invisibles
        if str(rol).strip() == "Cliente":
            st.info("Entré al IF de CLIENTE")
            st.page_link("pages/Catalogo.py", label="Ir al Catálogo", icon="🛒")

        elif str(rol).strip() == "Admin":
            st.info("Entré al IF de ADMIN")
            st.page_link("app.py", label="Inicio", icon="🏠")
            st.page_link("pages/Dashboard_Demanda.py", label="Demanda", icon="📊")
            # Agrega aquí el resto de tus páginas...

        else:
            st.error("⚠️ El rol no coincide con ningún IF")

        st.divider()
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.rerun()
