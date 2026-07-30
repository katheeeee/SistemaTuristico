# src/reentrenar.py
import sys
import os
_src_dir = os.path.dirname(__file__)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
_parent = os.path.dirname(_src_dir)
if _parent not in sys.path:
    sys.path.insert(0, _parent)


def reentrenar_modelos(epochs_lightgcn=15):
    from datos_puno import recargar_datos
    from lightgcn_model import entrenar_lightgcn
    from preparar_meta_dataset import generar_dataset, entrenar_meta_recomendador
    import joblib

    print("=== Reentrenando modelos ===")

    recargar_datos()

    print("[1/2] LightGCN...")
    try:
        entrenar_lightgcn(epochs=epochs_lightgcn)
    except Exception as e:
        print(f"  Error LightGCN: {e}")

    print("[2/2] Meta-recommender...")
    try:
        df = generar_dataset()
        modelo = entrenar_meta_recomendador(df)
        joblib.dump(modelo, "meta_recomendador.pkl")
        print(f"  Meta-recommender guardado ({len(df)} pares)")
    except Exception as e:
        print(f"  Error Meta: {e}")

    print("=== Reentrenamiento completado ===")
