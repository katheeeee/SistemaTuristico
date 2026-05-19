# src/grafo_hibrido.py
import networkx as nx
from src.datos_puno import atractivos, usuarios

def construir_grafo_hibrido():
    """
    Construye un grafo híbrido que combina:
    - Nodos: usuarios, atractivos
    - Aristas: preferencias (colaborativo) y similitudes (contenido)
    """
    G = nx.Graph()
    
    # Agregar nodos de atractivos
    for a in atractivos:
        G.add_node(a["id"], 
                   tipo="atractivo", 
                   nombre=a["nombre"], 
                   tipo_atractivo=a["tipo"],
                   zona=a["zona"],
                   popularidad=a["popularidad"])
    
    # Agregar nodos de usuarios
    for u in usuarios:
        G.add_node(u["id"], 
                   tipo="usuario", 
                   nombre=u["nombre"],
                   preferencias=u["preferencias"])
    
    # --- Aristas colaborativas (usuario → atractivo por preferencia) ---
    for u in usuarios:
        for a in atractivos:
            if a["tipo"] in u["preferencias"]:
                G.add_edge(u["id"], a["id"], 
                           relacion="prefiere", 
                           peso=1.0, 
                           tipo_arista="colaborativa")
    
    # --- Aristas de contenido (atractivo → atractivo por similitud) ---
    for i, a1 in enumerate(atractivos):
        for a2 in atractivos[i+1:]:
            peso = 0.0
            if a1["tipo"] == a2["tipo"]:
                peso = 0.9
            elif a1["zona"] == a2["zona"]:
                peso = 0.6
            if peso > 0:
                G.add_edge(a1["id"], a2["id"], 
                           relacion="similar", 
                           peso=peso,
                           tipo_arista="contenido")
    
    return G

# Instancia global (opcional, para importar fácil)
G_hibrido = construir_grafo_hibrido()