# ============================================
# modules/anomalia.py
# ============================================
import pandas as pd
from datetime import datetime

def detectar_anomalias_en_ventas():
    """Detecta valores atípicos en los registros de venta"""
    from conexion_db import get_connection
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor_total = conn.cursor()
    cursor_total.execute("""
        SELECT COUNT(*) 
        FROM evento_usuario
        WHERE tipo_evento = 'compra'
    """)
    total_compras_usuarios = cursor_total.fetchone()[0]

    cursor.execute("""
        SELECT 
            id_usuario, 
            id_item AS id_producto,
            COUNT(*) AS num_compras
        FROM evento_usuario
        WHERE tipo_evento = 'compra'
        GROUP BY id_usuario, id_item
        HAVING COUNT(*) > 3
    """)
    compras_repetidas = cursor.fetchall()

    reglas_extra = []
    for fila in compras_repetidas:
        reglas_extra.append({
            "id_usuario": fila[0],
            "id_producto": fila[1],
            "cantidad_compras": fila[2],
            "nivel": "medio" if fila[2] <= 10 else "alto"
        })

    cursor.execute("""
        SELECT id_venta, id_usuario, id_producto, cantidad, precio_unitario, 
               COALESCE(publicidad, 0) AS publicidad
        FROM venta
    """)
    data = cursor.fetchall()

    if not data:
        if not reglas_extra:
            conn.close()
            return {
                "mensaje": "No existen registros de venta para analizar.",
                "total_analizadas": 0,
                "anomalias": 0,
                "modelo": None,
                "detalles": []
            }

        id_modelo = registrar_modelo_anomalias(cursor, "SOLO_EVENTOS")
        conn.commit()
        conn.close()

        anomalias_lista = []
        for r in reglas_extra:
            anomalias_lista.append({
                "id_venta": "N/A",
                "id_usuario": r["id_usuario"],
                "id_producto": r["id_producto"],
                "total": "N/A",
                "cantidad": r["cantidad_compras"],
                "nivel": r["nivel"]
            })

        return {
            "mensaje": f"Se detectaron {len(anomalias_lista)} anomalías por compras repetidas.",
            "total_analizadas": 0,
            "anomalias": len(anomalias_lista),
            "modelo": id_modelo,
            "detalles": anomalias_lista
        }

    df = pd.DataFrame(data, columns=[
        "id_venta", "id_usuario", "id_producto",
        "cantidad", "precio_unitario", "publicidad"
    ])
    df["total"] = df["cantidad"] * df["precio_unitario"] + df["publicidad"]

    if len(df) == 1:
        conn.close()
        anomalias_lista = []
        for r in reglas_extra:
            anomalias_lista.append({
                "id_venta": "N/A",
                "id_usuario": r["id_usuario"],
                "id_producto": r["id_producto"],
                "total": "N/A",
                "cantidad": r["cantidad_compras"],
                "nivel": r["nivel"]
            })

        return {
            "mensaje": "Solo existe una venta registrada.",
            "total_analizadas": 1,
            "anomalias": len(anomalias_lista),
            "modelo": None,
            "detalles": anomalias_lista
        }

    total_series = df["total"]
    media_total = total_series.mean()
    desviacion_total = total_series.std(ddof=0)
    q1 = total_series.quantile(0.25)
    q3 = total_series.quantile(0.75)
    iqr = q3 - q1
    mediana = total_series.median()

    if len(df) >= 5 and iqr > 0:
        umbral_inf = max(0, q1 - 1.5 * iqr)
        umbral_sup = q3 + 1.5 * iqr
        metodo = "IQR"
    elif desviacion_total > 0:
        umbral_inf = max(0, media_total - 2 * desviacion_total)
        umbral_sup = media_total + 2 * desviacion_total
        metodo = "MEDIA+DESV"
    else:
        umbral_inf = 0
        umbral_sup = mediana * 2
        metodo = "REGLA_MEDIANA"

    UMBRAL_CANTIDAD_ALTA = 3

    condiciones_total = (df["total"] < umbral_inf) | (df["total"] > umbral_sup)
    condiciones_cantidad = df["cantidad"] > UMBRAL_CANTIDAD_ALTA

    anomalias_detectadas = df[condiciones_total | condiciones_cantidad].copy()

    id_modelo = registrar_modelo_anomalias(cursor, metodo)

    registros = []
    anomalias_lista = []

    for _, row in anomalias_detectadas.iterrows():
        valor_total = row["total"]
        cant = row["cantidad"]

        if metodo == "IQR":
            muy_extremo_monto = (valor_total > q3 + 3 * iqr) or (valor_total < q1 - 3 * iqr)
        elif metodo == "MEDIA+DESV":
            muy_extremo_monto = (valor_total > media_total + 3 * desviacion_total) or (
                valor_total < max(0, media_total - 3 * desviacion_total)
            )
        else:
            muy_extremo_monto = valor_total > mediana * 3

        muy_extremo_cantidad = cant > (UMBRAL_CANTIDAD_ALTA * 2)

        nivel = "alto" if (muy_extremo_monto or muy_extremo_cantidad) else "medio"

        descripcion = (
            f"Venta fuera del rango esperado (método: {metodo}). "
            f"Total {valor_total:.2f}, media {media_total:.2f}, mediana {mediana:.2f}, "
            f"cantidad={cant}"
        )

        registros.append((
            id_modelo,
            int(row["id_venta"]),
            descripcion,
            f"total={valor_total:.2f}; cantidad={cant}",
            nivel
        ))

        anomalias_lista.append({
            "id_venta": int(row["id_venta"]),
            "id_usuario": int(row["id_usuario"]),
            "id_producto": int(row["id_producto"]),
            "total": float(valor_total),
            "cantidad": int(cant),
            "nivel": nivel
        })

    if registros:
        cursor.executemany("""
            INSERT INTO anomalia (id_modelo, id_venta, descripcion, valor_detectado, nivel)
            VALUES (?, ?, ?, ?, ?)
        """, registros)

    for r in reglas_extra:
        anomalias_lista.append({
            "id_venta": "N/A",
            "id_usuario": r["id_usuario"],
            "id_producto": r["id_producto"],
            "total": "N/A",
            "cantidad": r["cantidad_compras"],
            "nivel": r["nivel"]
        })

    conn.commit()
    conn.close()

    return {
        "mensaje": f"Se detectaron {len(anomalias_lista)} anomalías. Método usado: {metodo}.",
        "total_analizadas": total_compras_usuarios,
        "anomalias": len(anomalias_lista),
        "modelo": id_modelo,
        "detalles": anomalias_lista
    }


def registrar_modelo_anomalias(cursor, metodo):
    """Registra el modelo de detección"""
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nombre = f"ModeloAnomalias_{metodo}_{fecha}"
    cursor.execute("""
        INSERT INTO modelo_ml 
            (nombre_modelo, tipo, version, fecha_entrenamiento, accuracy, mae, archivo_modelo, estado)
        VALUES (?, 'anomalias', 'v1.1', ?, 1.0, 0.0, '-', 'entrenado')
    """, (nombre, fecha))
    return cursor.lastrowid

