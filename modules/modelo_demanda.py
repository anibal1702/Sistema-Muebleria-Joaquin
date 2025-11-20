# ============================================
# modules/modelo_demanda.py
# ============================================
import pandas as pd
from datetime import datetime
from conexion_db import get_connection

def entrenar_modelo_demanda():
    """Entrena modelo de predicción de demanda"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_item, COUNT(*) AS ventas
        FROM evento_usuario
        WHERE tipo_evento = 'compra'
        GROUP BY id_item
    """)
    data = cursor.fetchall()

    if not data:
        conn.close()
        raise ValueError("No hay datos suficientes para entrenar el modelo")

    df = pd.DataFrame(data, columns=['id_producto', 'ventas'])
    df['indice'] = range(1, len(df) + 1)

    x = df['indice']
    y = df['ventas']

    n = len(df)
    split_idx = max(1, int(n * 0.7))
    if split_idx >= n:
        split_idx = n - 1

    x_train = x.iloc[:split_idx]
    y_train = y.iloc[:split_idx]
    x_test = x.iloc[split_idx:]
    y_test = y.iloc[split_idx:]

    x_mean = x_train.mean()
    y_mean = y_train.mean()
    m = ((x_train - x_mean) * (y_train - y_mean)).sum() / ((x_train - x_mean) ** 2).sum()
    b = y_mean - m * x_mean

    y_train_pred = m * x_train + b
    y_test_pred = m * x_test + b

    mae_train = (y_train - y_train_pred).abs().mean()
    mae_test = (y_test - y_test_pred).abs().mean()

    df['prediccion'] = m * df['indice'] + b
    df['error_abs'] = (df['ventas'] - df['prediccion']).abs()

    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    modelo_filename = f"modelo_demanda_{fecha}.csv"
    df.to_csv(modelo_filename, index=False)

    cursor.execute("""
        INSERT INTO modelo_ml (
            nombre_modelo, tipo, version, fecha_entrenamiento,
            accuracy, mae, archivo_modelo, estado
        )
        VALUES (?, 'prediccion_demanda', ?, ?, ?, ?, ?, 'entrenado')
    """, (
        f"ModeloDemanda_{fecha}",
        "v1.0",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        1.0,
        float(mae_test),
        modelo_filename
    ))

    id_modelo = cursor.lastrowid

    predicciones = [
        (id_modelo, row['id_producto'], datetime.now().strftime("%Y-%m-%d"), 
         int(round(row['prediccion'])))
        for _, row in df.iterrows()
    ]

    cursor.executemany("""
        INSERT INTO prediccion_demanda (id_modelo, id_producto, fecha_prediccion, demanda_esperada)
        VALUES (?, ?, ?, ?)
    """, predicciones)

    conn.commit()
    conn.close()

    resumen_df = df[['id_producto', 'ventas', 'prediccion', 'error_abs']].copy()
    resumen_df['prediccion'] = resumen_df['prediccion'].round(2)
    resumen_df['error_abs'] = resumen_df['error_abs'].round(2)

    return {
        "archivo": modelo_filename,
        "mae_train": round(float(mae_train), 3),
        "mae_test": round(float(mae_test), 3),
        "resumen": resumen_df.to_dict(orient='records')
    }

