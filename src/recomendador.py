# src/recomendador.py
import random
from src.grafo_hibrido import G_hibrido

def recomendar(usuario_id, num_walks=200, walk_length=5, restart_prob=0.2):
    if usuario_id not in G_hibrido:
        return []
    
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
    
    return sorted(conteos.items(), key=lambda x: x[1], reverse=True)[:10]