# src/recomendador.py
import random
from datos_puno import G_hibrido

def recomendar_popularidad(usuario_id=None, top_n=10):
    """Recomienda los atractivos más populares (mayor grado en el grafo)."""
    popularidad = []
    for node, attrs in G_hibrido.nodes(data=True):
        if attrs.get('tipo') == 'atractivo':
            grado = G_hibrido.degree(node)
            popularidad.append((node, grado))
    popularidad.sort(key=lambda x: x[1], reverse=True)
    return [(node, score) for node, score in popularidad[:top_n]]

def recomendar(usuario_id, num_walks=200, walk_length=5, restart_prob=0.2):
    if usuario_id not in G_hibrido:
        return recomendar_popularidad(usuario_id)
    
    # Si el usuario no tiene vecinos, fallback a popularidad
    if G_hibrido.degree(usuario_id) == 0:
        return recomendar_popularidad(usuario_id)
    
    conteos = {}
    for _ in range(num_walks):
        nodo = usuario_id
        for _ in range(walk_length):
            if random.random() < restart_prob:
                nodo = usuario_id
            else:
                vecinos = list(G_hibrido.neighbors(nodo))
                if vecinos:
                    pesos = [G_hibrido[nodo][v].get("peso", 1.0) for v in vecinos]
                    total = sum(pesos)
                    if total == 0:
                        nodo = random.choice(vecinos)
                    else:
                        probs = [p/total for p in pesos]
                        nodo = random.choices(vecinos, weights=probs, k=1)[0]
                else:
                    break
            
            if G_hibrido.nodes[nodo].get("tipo") == "atractivo":
                conteos[nodo] = conteos.get(nodo, 0) + 1
    
    # Si no se encontraron atractivos, usar popularidad
    if not conteos:
        return recomendar_popularidad(usuario_id)
    
    return sorted(conteos.items(), key=lambda x: x[1], reverse=True)[:10]