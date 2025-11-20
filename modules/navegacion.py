import streamlit as st
import os

def mostrar_menu_lateral():
    if 'rol' not in st.session_state:
        return

    # Limpieza
    rol_original = st.session_state['rol']
    rol_limpio = str(rol_original).strip().upper() # Forzamos texto y mayúsculas
    nombre = st.session_state.get('nombre', 'Usuario')

    with st.sidebar:
        st.write(f"👤 **{nombre}**")
        
        # --- ZONA DE DIAGNÓSTICO (Bórrala luego) ---
        st.error(f"🕵️ DEBUG: Rol detectado -> [{rol_limpio}]")
        # ------------------------------------------

        st.divider()

        # --- LOGICA CLIENTE ---
        if rol_limpio == "CLIENTE":
            st.success("✅ Entró al bloque CLIENTE") # CHIVATO 1
            
            # Intentamos mostrar el link
            try:
                st.page_link("pages/Catalogo.py", label="Ir al Catálogo", icon="🛒")
            except Exception as e:
                st.error(f"❌ Error mostrando el link: {e}")

        # --- LOGICA ADMIN ---
        elif rol_limpio == "ADMIN":
            st.success("✅ Entró al bloque ADMIN") # CHIVATO 2
            st.page_link("app.py", label="Inicio", icon="🏠")
            st.page_link("pages/Catalogo.py", label="Catálogo", icon="🛒")
            st.page_link("pages/Dashboard_Demanda.py", label="Demanda", icon="📊")
            # ... puedes agregar los demás luego ...

        else:
            st.warning("⚠️ No coincidió con nadie") # CHIVATO 3

        st.divider()
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.rerun()
