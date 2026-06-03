# src/grafo_hibrido.py
# Este módulo reexporta el grafo y las estructuras ya construidas en datos_puno.py
# para mantener compatibilidad con los demás módulos (recomendador, lightgcn_model, etc.)

from datos_puno import G_hibrido, usuarios, atractivos

# Opcional: si quieres tener una función con el nombre antiguo (por si algún módulo la llama)
def construir_grafo_hibrido():
    return G_hibrido