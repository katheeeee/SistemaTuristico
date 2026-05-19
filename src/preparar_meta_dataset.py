# src/preparar_meta_dataset.py
import numpy as np
import pandas as pd
from itertools import product
from datos_puno import usuarios, atractivos
from grafo_hibrido import G_hibrido
from recomendador import recomendar as random_walk_recommend

def obtener_puntuacion_random_walk(usuario_id, atractivo_id):
    """Obtiene la puntuación que el random walk asigna a un par específico."""
    # Ejecuta random walk y obtiene diccionario de puntuaciones
    recs = dict(random_walk_recommend(usuario_id, num_walks=100))
    return recs.get(atractivo_id, 0.0)

def obtener_puntuacion_popularidad(atractivo_id):
    """Popularidad del atractivo (proporción de usuarios que lo tienen en preferencias)."""
    contador = 0
    for u in usuarios:
        # Ver si el atractivo coincide con alguna preferencia del usuario
        atractivo_obj = next((a for a in atractivos if a["id"] == atractivo_id), None)
        if atractivo_obj and atractivo_obj["tipo"] in u["preferencias"]:
            contador += 1
    return contador / len(usuarios)

def generar_dataset():
    """Genera un DataFrame con características y etiqueta para cada par (usuario, atractivo)."""
    data = []
    user_ids = [u["id"] for u in usuarios]
    item_ids = [a["id"] for a in atractivos]
    
    # Construir matriz de interacciones real (etiqueta) desde el grafo
    interacciones_reales = {}
    for u_id in user_ids:
        for a_id in item_ids:
            if G_hibrido.has_edge(u_id, a_id):
                interacciones_reales[(u_id, a_id)] = 1
            else:
                interacciones_reales[(u_id, a_id)] = 0
    
    # Para cada par, calcular características
    for u_id, a_id in product(user_ids, item_ids):
        rw_score = obtener_puntuacion_random_walk(u_id, a_id)
        pop_score = obtener_puntuacion_popularidad(a_id)
        data.append({
            "usuario": u_id,
            "atractivo": a_id,
            "rw_score": rw_score,
            "popularidad": pop_score,
            "interaccion": interacciones_reales[(u_id, a_id)]
        })
    
    df = pd.DataFrame(data)
    return df

def entrenar_meta_recomendador(df):
    """Entrena un clasificador (regresión logística) para predecir la interacción."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    
    X = df[["rw_score", "popularidad"]].values
    y = df["interaccion"].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LogisticRegression(class_weight="balanced")
    model.fit(X_train, y_train)
    
    print(f"Precisión en entrenamiento: {model.score(X_train, y_train):.3f}")
    print(f"Precisión en prueba: {model.score(X_test, y_test):.3f}")
    return model