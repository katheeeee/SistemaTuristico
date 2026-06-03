# src/lightgcn_model.py
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from datos_puno import usuarios, atractivos, G_hibrido

# ------------------------------------------------------------
# Modelo LightGCN
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Construcción de matriz de interacciones
# ------------------------------------------------------------
def construir_matriz_interacciones():
    num_users = len(usuarios)
    num_items = len(atractivos)
    matriz = np.zeros((num_users, num_items), dtype=np.float32)
    user_index = {u["id"]: i for i, u in enumerate(usuarios)}
    item_index = {a["id"]: i for i, a in enumerate(atractivos)}
    for u, v, data in G_hibrido.edges(data=True):
        if data.get("relacion") in ["prefiere", "interes_zona", "visito"]:
            if u in user_index and v in item_index:
                peso = data.get("peso", 1.0)
                matriz[user_index[u], item_index[v]] = peso
            elif v in user_index and u in item_index:
                peso = data.get("peso", 1.0)
                matriz[user_index[v], item_index[u]] = peso
    return matriz, user_index, item_index

# ------------------------------------------------------------
# Entrenamiento
# ------------------------------------------------------------
def entrenar_lightgcn(epochs=30, embed_dim=32, n_layers=2, lr=0.01):
    matriz, user_index, item_index = construir_matriz_interacciones()
    num_users, num_items = matriz.shape
    user_ids, item_ids = np.where(matriz > 0)
    print(f"LightGCN: entrenando con {len(user_ids)} interacciones positivas, {num_users} usuarios, {num_items} ítems")
    if len(user_ids) == 0:
        raise ValueError("No hay interacciones positivas para entrenar LightGCN.")
    
    model = LightGCN(num_users, num_items, embed_dim, n_layers)
    optimizer = optim.Adam(model.parameters(), lr=lr)

    edge_index = np.vstack([user_ids, item_ids + num_users])
    edge_index = torch.tensor(edge_index, dtype=torch.long)

    positivos = list(zip(user_ids, item_ids))
    model.train()

    for epoch in range(epochs):
        total_loss = 0.0
        for u, i in positivos:
            neg = np.random.randint(0, num_items)
            while neg == i:
                neg = np.random.randint(0, num_items)
            u_t = torch.tensor([u], dtype=torch.long)
            i_t = torch.tensor([i], dtype=torch.long)
            neg_t = torch.tensor([neg], dtype=torch.long)

            user_emb, item_emb = model(edge_index)
            loss = model.bpr_loss(user_emb[u_t], item_emb[i_t], item_emb[neg_t])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(positivos)
        print(f"Epoch {epoch+1:3d}/{epochs} - Loss: {avg_loss:.6f}")

    torch.save(model.state_dict(), "lightgcn_model.pth")
    import joblib
    joblib.dump((user_index, item_index, num_users, num_items), "lightgcn_mappings.pkl")
    return model, user_index, item_index

# ------------------------------------------------------------
# Carga del modelo
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Recomendación (corregida)
# ------------------------------------------------------------
def recomendar_lightgcn(usuario_id, top_n=10):
    model, user_index, item_index = cargar_lightgcn()
    if model is None or usuario_id not in user_index:
        print(f"LightGCN: modelo no cargado o usuario '{usuario_id}' no encontrado")
        return []
    u_idx = user_index[usuario_id]
    num_users = len(user_index)
    num_items = len(item_index)

    matriz, _, _ = construir_matriz_interacciones()
    user_ids, item_ids = np.where(matriz > 0)
    if len(user_ids) == 0:
        return []
    edge_index = np.vstack([user_ids, item_ids + num_users])
    edge_index = torch.tensor(edge_index, dtype=torch.long)

    with torch.no_grad():
        user_emb, item_emb = model(edge_index)
        scores = item_emb @ user_emb[u_idx]

    k = min(top_n, num_items)
    if k <= 0:
        return []
    top_indices = torch.topk(scores, k=k).indices.numpy()
    inv_item_index = {v: k for k, v in item_index.items()}
    resultados = [(inv_item_index[idx], float(scores[idx])) for idx in top_indices]
    return resultados   # ← CORREGIDO: antes decía 'return resultadospy'