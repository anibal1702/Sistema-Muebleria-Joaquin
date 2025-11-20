# ============================================
# modules/conexion_db.py
# ============================================
import sqlite3
from datetime import datetime
import pandas as pd
import os

def get_connection():
    """Obtiene conexión a la base de datos"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'Data_muebles_db.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def registrar_venta(id_usuario, id_producto, cantidad, precio_unitario, publicidad=0.0):
    """Registra una venta en la tabla 'venta'"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fecha_venta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO venta (id_usuario, id_producto, cantidad, precio_unitario, publicidad, fecha_venta)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (id_usuario, id_producto, cantidad, precio_unitario, publicidad, fecha_venta))
    
    conn.commit()
    id_venta = cursor.lastrowid
    conn.close()
    
    return id_venta

def verify_user(user, passw):
    """Verifica credenciales de usuario"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id_usuario, nombre, rol FROM usuario WHERE user=? AND pass=?", (user, passw))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return (result[0], result[1], result[2])
    else:
        return None

def create_user(name, user, correo, passw):
    """Crea un nuevo usuario"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO usuario (nombre, user, correo, pass) VALUES (?,?,?,?)",
            (name, user, correo, passw)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        print("Error: el usuario ya existe o datos inválidos.", e)
        return False
    finally:
        conn.close()

def get_all_products():
    """Obtiene todos los productos"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_producto, nombre, descripcion, categoria, precio, stock FROM producto")
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

def get_recomendaciones_usuario(id_usuario, limite=3):
    """Obtiene recomendaciones para un usuario"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            r.id_producto,
            p.nombre,
            p.categoria,
            p.precio,
            p.stock,
            p.descripcion
        FROM recomendacion r
        JOIN producto p ON r.id_producto = p.id_producto
        WHERE r.id_usuario = ?
        ORDER BY r.puntaje_recomendacion DESC
        LIMIT ?
    """, (id_usuario, limite))
    
    rows = cursor.fetchall()
    conn.close()
    
    productos = []
    for row in rows:
        productos.append({
            "id_producto": row[0],
            "nombre": row[1],
            "categoria": row[2],
            "precio": row[3],
            "stock": row[4],
            "descripcion": row[5]
        })
    
    return productos

def export_eventos_to_excel(filename="eventos_usuarios.xlsx"):
    """Exporta eventos a Excel"""
    try:
        conn = get_connection()
        query = "SELECT * FROM evento_usuario ORDER BY timestamp DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return None
        
        df.to_excel(filename, index=False)
        return filename
    except Exception as e:
        print(f"Error al exportar: {e}")
        return None

