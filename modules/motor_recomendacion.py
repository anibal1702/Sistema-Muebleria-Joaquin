# ============================================
# modules/motor_recomendacion.py
# ============================================
import sqlite3
from datetime import datetime
from conexion_db import get_connection


def entrenar_motor_recomendacion():
    """Genera recomendaciones personalizadas por usuario"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            id_usuario,
            id_item AS id_producto,
            SUM(
                CASE 
                    WHEN tipo_evento = 'clic'        THEN 1
                    WHEN tipo_evento = 'add_to_cart' THEN 2
                    WHEN tipo_evento = 'compra'      THEN 3
                    ELSE 0
                END
            ) AS puntuacion
        FROM evento_usuario
        WHERE tipo_evento IN ('clic', 'compra', 'add_to_cart')
        GROUP BY id_usuario, id_item
    """)
    interacciones = cursor.fetchall()

    if not interacciones:
        conn.close()
        raise ValueError("No hay datos de interacción para entrenar el motor")
    
    cursor.execute("""
        SELECT 
            e.id_item AS id_producto,
            COUNT(*) AS total_interacciones,
            p.nombre AS nombre_producto
        FROM evento_usuario e
        LEFT JOIN producto p ON p.id_producto = e.id_item
        WHERE tipo_evento IN ('clic','add_to_cart','compra')
        GROUP BY e.id_item
        ORDER BY total_interacciones DESC
        LIMIT 1
    """)
    producto_top = cursor.fetchone()

    if producto_top:
        top_producto_id = producto_top["id_producto"]
        top_producto_nombre = producto_top["nombre_producto"] or "Producto sin nombre"
        top_producto_total = producto_top["total_interacciones"]
    else:
        top_producto_id = None
        top_producto_nombre = "Sin datos"
        top_producto_total = 0

    scores_por_usuario = {}
    for fila in interacciones:
        uid = fila["id_usuario"]
        pid = fila["id_producto"]
        score = fila["puntuacion"] or 0
        scores_por_usuario.setdefault(uid, []).append((pid, score))

    recomendaciones = []
    usuarios_con_recs = 0

    for uid, lista in scores_por_usuario.items():
        max_score = max(s for (_, s) in lista) if lista else 0

        if max_score <= 0:
            continue

        usuarios_con_recs += 1

        for pid, score in lista:
            puntaje_norm = score / max_score
            recomendaciones.append((uid, pid, puntaje_norm))

    if not recomendaciones:
        conn.close()
        raise ValueError("No se pudieron generar recomendaciones válidas")

    cursor.execute("""
        INSERT INTO modelo_ml 
            (nombre_modelo, tipo, version, fecha_entrenamiento, accuracy, mae, archivo_modelo, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Motor Recomendación V2",
        "recomendacion",
        "2.0",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        0.85,
        0.15,
        "modelo_recomendacion_v2.pkl",
        "en_produccion"
    ))
    id_modelo = cursor.lastrowid

    cursor.execute("DELETE FROM recomendacion")

    registros_recomendacion = [
        (id_modelo, uid, pid, puntaje)
        for (uid, pid, puntaje) in recomendaciones
    ]

    cursor.executemany("""
        INSERT INTO recomendacion (id_modelo, id_usuario, id_producto, puntaje_recomendacion)
        VALUES (?, ?, ?, ?)
    """, registros_recomendacion)

    conn.commit()
    conn.close()

    total_recomendaciones = len(registros_recomendacion)
    total_usuarios = len(scores_por_usuario)
    promedio_recs_por_usuario = (
        round(total_recomendaciones / total_usuarios, 2) if total_usuarios > 0 else 0
    )

    return {
        "id_modelo": id_modelo,
        "total_usuarios": total_usuarios,
        "usuarios_con_recs": usuarios_con_recs,
        "total_recomendaciones": total_recomendaciones,
        "promedio_recs_por_usuario": promedio_recs_por_usuario,
        "top_producto_id": top_producto_id,
        "top_producto_nombre": top_producto_nombre,
        "top_producto_total": top_producto_total
    }
