# entrenar_lightgcn.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from lightgcn_model import entrenar_lightgcn

if __name__ == "__main__":
    print("=== ENTRENAMIENTO LIGHTGCN ===")
    modelo, user_idx, item_idx = entrenar_lightgcn(epochs=30)
    print("Entrenamiento completado. Modelo guardado como 'lightgcn_model.pth'")
    print(f"Usuarios mapeados: {len(user_idx)}")
    print(f"Atractivos mapeados: {len(item_idx)}")