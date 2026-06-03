# src/preparar_meta_dataset.py
import numpy as np
import pandas as pd
import random
from itertools import product
from datos_puno import usuarios, atractivos, G_hibrido
from recomendador import recomendar as random_walk_recommend

def obtener_puntuacion_random_walk(usuario_id, atractivo_id):
    recs = dict(random_walk_recommend(usuario_id))
    return recs.get(atractivo_id, 0.0)

def obtener_puntuacion_popularidad(atractivo_id):
    contador = 0
    for u in usuarios:
        if G_hibrido.has_edge(u["id"], atractivo_id):
            contador += 1
    return contador / len(usuarios) if len(usuarios) > 0 else 0

def generar_dataset(neg_ratio=1.0):
    """
    Genera dataset balanceado con muestreo negativo.
    Como todos los pares son positivos, los negativos se generan aleatoriamente
    sin comprobar si son realmente negativos (simplificación para demostración).
    """
    data = []
    user_ids = [u["id"] for u in usuarios]
    item_ids = [a["id"] for a in atractivos]
    
    # 1. Lista de pares positivos (interacción real)
    positivos = []
    for u_id in user_ids:
        for a_id in item_ids:
            if G_hibrido.has_edge(u_id, a_id):
                positivos.append((u_id, a_id))
    
    print(f"Positivos encontrados: {len(positivos)}")
    
    # 2. Generar negativos aleatorios (sin comprobación)
    num_neg = int(len(positivos) * neg_ratio)
    negativos = []
    for _ in range(num_neg):
        u = random.choice(user_ids)
        a = random.choice(item_ids)
        negativos.append((u, a))
    
    print(f"Negativos generados (pueden incluir falsos negativos): {len(negativos)}")
    
    # 3. Unir y calcular características
    for u_id, a_id in positivos:
        rw = obtener_puntuacion_random_walk(u_id, a_id)
        pop = obtener_puntuacion_popularidad(a_id)
        data.append({
            "usuario": u_id,
            "atractivo": a_id,
            "rw_score": rw,
            "popularidad": pop,
            "interaccion": 1
        })
    
    for u_id, a_id in negativos:
        rw = obtener_puntuacion_random_walk(u_id, a_id)
        pop = obtener_puntuacion_popularidad(a_id)
        data.append({
            "usuario": u_id,
            "atractivo": a_id,
            "rw_score": rw,
            "popularidad": pop,
            "interaccion": 0
        })
    
    df = pd.DataFrame(data)
    return df

def entrenar_meta_recomendador(df):
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    
    X = df[["rw_score", "popularidad"]].values
    y = df["interaccion"].values
    
    if len(np.unique(y)) < 2:
        raise ValueError("El dataset debe contener al menos dos clases (0 y 1).")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LogisticRegression(class_weight="balanced")
    model.fit(X_train, y_train)
    
    print(f"Precisión en entrenamiento: {model.score(X_train, y_train):.3f}")
    print(f"Precisión en prueba: {model.score(X_test, y_test):.3f}")
    return model