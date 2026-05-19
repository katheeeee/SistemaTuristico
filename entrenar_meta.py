# entrenar_meta.py
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.preparar_meta_dataset import generar_dataset, entrenar_meta_recomendador  # añade src.

import joblib

print("Generando dataset de entrenamiento...")
df = generar_dataset()
print(f"Dataset generado con {len(df)} pares (usuario, atractivo)")

print("Entrenando meta-recomendador...")
modelo = entrenar_meta_recomendador(df)

# Guardar el modelo para usarlo en la demo
joblib.dump(modelo, "meta_recomendador.pkl")
print("Modelo guardado como 'meta_recomendador.pkl'")