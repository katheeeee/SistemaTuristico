# src/preparar_meta_dataset.py
import numpy as np
import pandas as pd
import random
from datos_puno import usuarios, atractivos, G_hibrido, obtener_rating
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

def generar_dataset(neg_ratio=1.0):
    """
    Genera dataset balanceado con muestreo negativo.
    Features: rw_score, popularidad, edad_norm, match_preferencias,
              satisfaccion, categoria_* (one-hot).
    """
    data = []
    user_ids = [u["id"] for u in usuarios]
    item_ids = [a["id"] for a in atractivos]
    categorias = _get_categorias()

    positivos = []
    for u_id in user_ids:
        for a_id in item_ids:
            if G_hibrido.has_edge(u_id, a_id):
                positivos.append((u_id, a_id))

    print(f"Positivos encontrados: {len(positivos)}")

    num_neg = int(len(positivos) * neg_ratio)
    negativos = []
    for _ in range(num_neg):
        u = random.choice(user_ids)
        a = random.choice(item_ids)
        negativos.append((u, a))

    print(f"Negativos generados: {len(negativos)}")

    def _filas(pares, etiqueta):
        filas = []
        for u_id, a_id in pares:
            rw = obtener_puntuacion_random_walk(u_id, a_id)
            pop = obtener_puntuacion_popularidad(a_id)
            edad = _edad_usuario(u_id)
            match = _match_preferencias(u_id, a_id)
            sat = _satisfaccion_atractivo(a_id)

            tipo = ""
            for a in atractivos:
                if a["id"] == a_id:
                    tipo = a.get("tipo", "").strip().lower()
                    break
            cat_vec = {f"cat_{c}": (1.0 if tipo == c else 0.0) for c in categorias}

            fila = {
                "usuario": u_id,
                "atractivo": a_id,
                "rw_score": rw,
                "popularidad": pop,
                "edad_norm": min(edad / 80.0, 1.0),
                "match_preferencias": match,
                "satisfaccion": sat,
                **cat_vec,
                "interaccion": etiqueta,
            }
            filas.append(fila)
        return filas

    data = _filas(positivos, 1) + _filas(negativos, 0)
    df = pd.DataFrame(data)
    return df

def entrenar_meta_recomendador(df):
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        roc_auc_score, confusion_matrix, classification_report,
    )

    feature_cols = [c for c in df.columns if c not in ("usuario", "atractivo", "interaccion")]
    X = df[feature_cols].values
    y = df["interaccion"].values

    if len(np.unique(y)) < 2:
        raise ValueError("El dataset debe contener al menos dos clases (0 y 1).")

    print(f"\n=== Evaluación Meta-recommender ===")
    print(f"Features ({len(feature_cols)}): {feature_cols}")
    print(f"Muestras totales: {len(df)} | Positivos: {(y==1).sum()} | Negativos: {(y==0).sum()}")

    # Cross-validation (5-fold)
    cv = StratifiedKFold(n_splits=min(5, (y==1).sum(), (y==0).sum()), shuffle=True, random_state=42)
    cv_scores = cross_val_score(LogisticRegression(class_weight="balanced", max_iter=500),
                                 X, y, cv=cv, scoring="roc_auc")
    print(f"AUC-ROC CV (5-fold): {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LogisticRegression(class_weight="balanced", max_iter=500)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print(f"\n--- Test Set Evaluation ---")
    print(f"Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall:    {recall_score(y_test, y_pred):.4f}")
    print(f"F1-score:  {f1_score(y_test, y_pred):.4f}")
    print(f"AUC-ROC:   {roc_auc_score(y_test, y_prob):.4f}")
    print(f"\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"  TN={cm[0,0]}  FP={cm[0,1]}")
    print(f"  FN={cm[1,0]}  TP={cm[1,1]}")

    # Feature importance (coeficientes)
    coefs = pd.Series(model.coef_[0], index=feature_cols).sort_values(key=abs, ascending=False)
    print(f"\n--- Feature Importance ---")
    for feat, coef in coefs.items():
        print(f"  {feat:30s} {coef:+.4f}")

    return model
