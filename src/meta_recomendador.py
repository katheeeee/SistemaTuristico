# src/meta_recomendador.py
import joblib
from datos_puno import usuarios, atractivos, G_hibrido, obtener_rating
from recomendador import recomendar as random_walk_recommend
from recomendador import recomendar_popularidad
from preparar_meta_dataset import obtener_puntuacion_popularidad

_modelo_meta = None

def _edad_usuario(usuario_id):
    for u in usuarios:
        if u["id"] == usuario_id:
            edad = u.get("edad")
            if edad is not None:
                try:
                    return float(edad)
                except (ValueError, TypeError):
                    return 0.0
    if usuario_id in G_hibrido.nodes:
        edad = G_hibrido.nodes[usuario_id].get("edad")
        if edad is not None:
            try:
                return float(edad)
            except (ValueError, TypeError):
                return 0.0
    return 0.0

def _match_preferencias(usuario_id, atractivo_id):
    prefs = []
    for u in usuarios:
        if u["id"] == usuario_id:
            prefs = u.get("preferencias", [])
            break
    if not prefs and usuario_id in G_hibrido.nodes:
        prefs = G_hibrido.nodes[usuario_id].get("preferencias", [])
    tipo = ""
    for a in atractivos:
        if a["id"] == atractivo_id:
            tipo = a.get("tipo", "")
            break
    if not tipo and atractivo_id in G_hibrido.nodes:
        tipo = G_hibrido.nodes[atractivo_id].get("tipo_atractivo", "")
    return 1.0 if tipo and tipo in prefs else 0.0

def _satisfaccion_atractivo(atractivo_id):
    nombre = None
    for a in atractivos:
        if a["id"] == atractivo_id:
            nombre = a.get("nombre", "")
            break
    if not nombre and atractivo_id in G_hibrido.nodes:
        nombre = G_hibrido.nodes[atractivo_id].get("nombre", "")
    return obtener_rating(nombre) if nombre else 4.0

def _get_categorias():
    cats = set()
    for a in atractivos:
        t = a.get("tipo", "").strip().lower()
        if t:
            cats.add(t)
    return sorted(cats)

def cargar_modelo():
    global _modelo_meta
    if _modelo_meta is None:
        try:
            _modelo_meta = joblib.load("meta_recomendador.pkl")
        except Exception:
            print("Modelo meta no encontrado. Ejecuta entrenar_meta.py primero.")
            _modelo_meta = None
    return _modelo_meta

def recomendar_meta(usuario_id, top_n=10):
    if usuario_id not in G_hibrido or G_hibrido.degree(usuario_id) == 0:
        print(f"Usuario {usuario_id} sin conexiones. Usando popularidad.")
        return recomendar_popularidad(usuario_id, top_n=top_n)

    model = cargar_modelo()
    if model is None:
        print("Modelo meta no disponible. Usando popularidad.")
        return recomendar_popularidad(usuario_id, top_n=top_n)

    categorias = _get_categorias()
    edad = _edad_usuario(usuario_id)
    edad_norm = min(edad / 80.0, 1.0) if edad > 0 else 0.0
    rw_recs = dict(random_walk_recommend(usuario_id))

    puntuaciones = []
    for a in atractivos:
        a_id = a["id"]
        rw_score = rw_recs.get(a_id, 0.0)
        pop_score = obtener_puntuacion_popularidad(a_id)
        match = _match_preferencias(usuario_id, a_id)
        sat = _satisfaccion_atractivo(a_id)
        tipo = a.get("tipo", "").strip().lower()
        cat_vec = [1.0 if tipo == c else 0.0 for c in categorias]

        features = [[rw_score, pop_score, edad_norm, match, sat] + cat_vec]
        prob = model.predict_proba(features)[0][1]
        puntuaciones.append((a_id, prob))

    puntuaciones.sort(key=lambda x: x[1], reverse=True)
    return puntuaciones[:top_n]
