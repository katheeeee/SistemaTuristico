# src/lightgcn_model.py
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from datos_puno import usuarios, atractivos
from grafo_hibrido import G_hibrido

class LightGCN(nn.Module):
    def __init__(self, num_users, num_items, embed_dim=32, n_layers=2):
        super().__init__()
        self.num_users = num_users
        self.num_items = num_items
        self.embed_dim = embed_dim
        self.n_layers = n_layers
        
        self.user_emb = nn.Embedding(num_users, embed_dim)
        self.item_emb = nn.Embedding(num_items, embed_dim)
        
        nn.init.normal_(self.user_emb.weight, std=0.1)
        nn.init.normal_(self.item_emb.weight, std=0.1)
    
    def forward(self, edge_index):
        all_emb = torch.cat([self.user_emb.weight, self.item_emb.weight], dim=0)
        embs = [all_emb]
        for _ in range(self.n_layers):
            all_emb = self._propagate(all_emb, edge_index)
            embs.append(all_emb)
        final_emb = torch.mean(torch.stack(embs, dim=0), dim=0)
        user_final, item_final = torch.split(final_emb, [self.num_users, self.num_items])
        return user_final, item_final
    
    def _propagate(self, emb, edge_index):
        src, dst = edge_index
        out = torch.zeros_like(emb)
        out[dst] += emb[src]
        return out
    
    def bpr_loss(self, user_emb, pos_item_emb, neg_item_emb):
        pos_score = (user_emb * pos_item_emb).sum(dim=1)
        neg_score = (user_emb * neg_item_emb).sum(dim=1)
        loss = -torch.log(torch.sigmoid(pos_score - neg_score)).mean()
        return loss

def construir_matriz_interacciones():
    num_users = len(usuarios)
    num_items = len(atractivos)
    matriz = np.zeros((num_users, num_items))
    user_index = {u["id"]: i for i, u in enumerate(usuarios)}
    item_index = {a["id"]: i for i, a in enumerate(atractivos)}
    
    for u, v, data in G_hibrido.edges(data=True):
        if data.get("relacion") in ["prefiere", "interes_zona"]:
            if u in user_index and v in item_index:
                matriz[user_index[u], item_index[v]] = 1
            elif v in user_index and u in item_index:
                matriz[user_index[v], item_index[u]] = 1
    return matriz, user_index, item_index

def entrenar_lightgcn(epochs=80, embed_dim=32, n_layers=2, lr=0.01):
    matriz, user_index, item_index = construir_matriz_interacciones()
    num_users, num_items = matriz.shape
    model = LightGCN(num_users, num_items, embed_dim, n_layers)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    # Edge index para propagación
    user_ids, item_ids = np.where(matriz == 1)
    edge_index = torch.tensor([user_ids, item_ids + num_users], dtype=torch.long)
    
    positivos = list(zip(user_ids, item_ids))
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for u, i in positivos:
            # muestreo negativo
            neg = np.random.randint(0, num_items)
            while matriz[u, neg] == 1:
                neg = np.random.randint(0, num_items)
            u_t = torch.tensor([u])
            i_t = torch.tensor([i])
            neg_t = torch.tensor([neg])
            user_emb, item_emb = model(edge_index)
            loss = model.bpr_loss(user_emb[u_t], item_emb[i_t], item_emb[neg_t])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch+1) % 20 == 0:
            print(f"Epoch {epoch+1}/{epochs} - Loss: {total_loss/len(positivos):.4f}")
    
    # Guardar modelo y mapeos
    torch.save(model.state_dict(), "lightgcn_model.pth")
    import joblib
    joblib.dump((user_index, item_index, num_users, num_items), "lightgcn_mappings.pkl")
    return model, user_index, item_index

def cargar_lightgcn(embed_dim=32, n_layers=2):
    from pathlib import Path
    if not Path("lightgcn_model.pth").exists():
        print("Modelo LightGCN no encontrado. Ejecuta entrenar_lightgcn() primero.")
        return None, None, None
    import joblib
    user_index, item_index, num_users, num_items = joblib.load("lightgcn_mappings.pkl")
    model = LightGCN(num_users, num_items, embed_dim, n_layers)
    model.load_state_dict(torch.load("lightgcn_model.pth", map_location=torch.device('cpu')))
    model.eval()
    return model, user_index, item_index

def recomendar_lightgcn(usuario_id, top_n=10):
    model, user_index, item_index = cargar_lightgcn()
    if model is None or usuario_id not in user_index:
        return []
    
    u_idx = user_index[usuario_id]
    num_users = len(user_index)
    num_items = len(item_index)
    # Reconstruir edge_index
    matriz, _, _ = construir_matriz_interacciones()
    user_ids, item_ids = np.where(matriz == 1)
    edge_index = torch.tensor([user_ids, item_ids + num_users], dtype=torch.long)
    with torch.no_grad():
        user_emb, item_emb = model(edge_index)
        scores = item_emb @ user_emb[u_idx]  # producto matriz-vector (num_items,)  # producto punto
    top_indices = torch.topk(scores, k=top_n).indices.numpy()
    # Mapear índices a ids de atractivos
    inv_item_index = {v: k for k, v in item_index.items()}
    resultados = [(inv_item_index[idx], float(scores[idx])) for idx in top_indices]
    return resultados