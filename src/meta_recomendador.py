# src/meta_recomendador.py
import joblib
from datos_puno import usuarios, atractivos          # sin el punto
from recomendador import recomendar as random_walk_recommend
from preparar_meta_dataset import obtener_puntuacion_popularidad   # sin el punto

_modelo_meta = None

def cargar_modelo():
    global _modelo_meta
    if _modelo_meta is None:
        try:
            _modelo_meta = joblib.load("meta_recomendador.pkl")
        except:
            print("Modelo no encontrado. Ejecuta entrenar_meta.py primero.")
            _modelo_meta = None
    return _modelo_meta

def recomendar_meta(usuario_id, top_n=10):
    """Usa el meta-modelo para puntuar todos los atractivos y devolver top-n."""
    model = cargar_modelo()
    if model is None:
        return []
    
    # Obtener puntuaciones de random walk para este usuario (diccionario id -> score)
    rw_recs = dict(random_walk_recommend(usuario_id))
    
    puntuaciones_finales = []
    for a in atractivos:
        a_id = a["id"]
        rw_score = rw_recs.get(a_id, 0.0)
        pop_score = obtener_puntuacion_popularidad(a_id)
        # Predecir probabilidad de interacción con el meta-modelo
        prob = model.predict_proba([[rw_score, pop_score]])[0][1]  # probabilidad de clase 1
        puntuaciones_finales.append((a_id, prob))
    
    # Ordenar por probabilidad descendente
    puntuaciones_finales.sort(key=lambda x: x[1], reverse=True)
    return puntuaciones_finales[:top_n]