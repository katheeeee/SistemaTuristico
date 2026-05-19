# entrenar_lightgcn.py
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.lightgcn_model import entrenar_lightgcn  # añade src.

print("Entrenando LightGCN...")
modelo, user_idx, item_idx = entrenar_lightgcn(epochs=80)
print("Modelo guardado como lightgcn_model.pth")