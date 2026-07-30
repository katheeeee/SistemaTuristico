# entrenar_meta.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from preparar_meta_dataset import generar_dataset, entrenar_meta_recomendador

import joblib

print("Generando dataset de entrenamiento...")
df = generar_dataset()
print(f"Dataset generado con {len(df)} pares (usuario, atractivo)")

print("Entrenando meta-recomendador...")
modelo = entrenar_meta_recomendador(df)

# Guardar el modelo para usarlo en la demo
joblib.dump(modelo, "meta_recomendador.pkl")
print("Modelo guardado como 'meta_recomendador.pkl'")