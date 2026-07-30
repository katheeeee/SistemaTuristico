# src/lightgcn_model.py
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from datos_puno import usuarios, atractivos, G_hibrido
from recomendador import recomendar_popularidad

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

    def build_adj_matrix(self, user_item_pairs):
        """Normalized adjacency: D^{-1/2} A D^{-1/2}, A = [0 R; R^T 0]"""
        n = self.num_users + self.num_items
        device = self.user_emb.weight.device
        A = torch.zeros((n, n), device=device)
        if user_item_pairs.size(1) > 0:
            src, dst = user_item_pairs
            A[src, dst + self.num_users] = 1.0
            A[dst + self.num_users, src] = 1.0
        deg = A.sum(dim=1)
        deg_inv_sqrt = deg.pow(-0.5)
        deg_inv_sqrt[deg == 0] = 0
        return torch.diag(deg_inv_sqrt) @ A @ torch.diag(deg_inv_sqrt)

    def forward(self, A_norm):
        all_emb = torch.cat([self.user_emb.weight, self.item_emb.weight], dim=0)
        embs = [all_emb]
        for _ in range(self.n_layers):
            all_emb = A_norm @ all_emb
            embs.append(all_emb)
        final_emb = torch.mean(torch.stack(embs, dim=0), dim=0)
        user_final, item_final = torch.split(final_emb, [self.num_users, self.num_items])
        return user_final, item_final

    def bpr_loss(self, user_emb, pos_item_emb, neg_item_emb):
        pos_score = (user_emb * pos_item_emb).sum(dim=1)
        neg_score = (user_emb * neg_item_emb).sum(dim=1)
        return -torch.log(torch.sigmoid(pos_score - neg_score)).mean()

def construir_matriz_interacciones():
    num_users = len(usuarios)
    num_items = len(atractivos)
    matriz = np.zeros((num_users, num_items), dtype=np.float32)
    user_index = {u["id"]: i for i, u in enumerate(usuarios)}
    item_index = {a["id"]: i for i, a in enumerate(atractivos)}
    for u, v, data in G_hibrido.edges(data=True):
        if data.get("relacion") in ["prefiere", "interes_zona", "visito"]:
            if u in user_index and v in item_index:
                matriz[user_index[u], item_index[v]] = data.get("peso", 1.0)
            elif v in user_index and u in item_index:
                matriz[user_index[v], item_index[u]] = data.get("peso", 1.0)
    return matriz, user_index, item_index

def entrenar_lightgcn(epochs=30, embed_dim=32, n_layers=2, lr=0.01):
    matriz, user_index, item_index = construir_matriz_interacciones()
    num_users, num_items = matriz.shape
    user_ids, item_ids = np.where(matriz > 0)
    print(f"LightGCN: {len(user_ids)} interacciones, {num_users} usuarios, {num_items} ítems")
    if len(user_ids) == 0:
        raise ValueError("No hay interacciones positivas para entrenar LightGCN.")

    model = LightGCN(num_users, num_items, embed_dim, n_layers)
    optimizer = optim.Adam(model.parameters(), lr=lr)

    u_t = torch.tensor(user_ids, dtype=torch.long)
    i_t = torch.tensor(item_ids, dtype=torch.long)
    edge_pairs = torch.stack([u_t, i_t])

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        A_norm = model.build_adj_matrix(edge_pairs)
        user_emb, item_emb = model(A_norm)

        neg = torch.randint(0, num_items, i_t.shape, dtype=torch.long)
        mask = neg == i_t
        while mask.any():
            n = mask.sum().item()
            neg[mask] = torch.randint(0, num_items, (n,), dtype=torch.long)
            mask = neg == i_t

        loss = model.bpr_loss(user_emb[u_t], item_emb[i_t], item_emb[neg])
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch+1:3d}/{epochs} - Loss: {loss.item():.6f}")

    torch.save(model.state_dict(), "lightgcn_model.pth")
    import joblib
    joblib.dump((user_index, item_index, num_users, num_items), "lightgcn_mappings.pkl")
    print(f"LightGCN: modelo guardado ({num_users} usuarios, {num_items} ítems, {len(user_ids)} interacciones)")
    return model, user_index, item_index

def cargar_lightgcn(embed_dim=32, n_layers=2):
    from pathlib import Path
    if not Path("lightgcn_model.pth").exists():
        print("Modelo LightGCN no encontrado. Ejecuta entrenar_lightgcn() primero.")
        return None, None, None
    import joblib
    try:
        user_index, item_index, num_users, num_items = joblib.load("lightgcn_mappings.pkl")
        model = LightGCN(num_users, num_items, embed_dim, n_layers)
        model.load_state_dict(torch.load("lightgcn_model.pth", map_location=torch.device('cpu')))
        model.eval()
        return model, user_index, item_index
    except Exception as e:
        print(f"LightGCN: error al cargar modelo (posible cambio en grafo): {e}")
        return None, None, None

def recomendar_lightgcn(usuario_id, top_n=10):
    if usuario_id not in G_hibrido or G_hibrido.degree(usuario_id) == 0:
        return recomendar_popularidad(usuario_id, top_n=top_n)

    try:
        model, user_index, item_index = cargar_lightgcn()
    except Exception:
        return recomendar_popularidad(usuario_id, top_n=top_n)

    if model is None or usuario_id not in user_index:
        return recomendar_popularidad(usuario_id, top_n=top_n)

    u_idx = user_index[usuario_id]
    num_users = len(user_index)
    num_items = len(item_index)

    matriz, _, _ = construir_matriz_interacciones()
    user_ids, item_ids = np.where(matriz > 0)
    if len(user_ids) == 0:
        return recomendar_popularidad(usuario_id, top_n=top_n)

    u_t = torch.tensor(user_ids, dtype=torch.long)
    i_t = torch.tensor(item_ids, dtype=torch.long)
    edge_pairs = torch.stack([u_t, i_t])

    try:
        with torch.no_grad():
            A_norm = model.build_adj_matrix(edge_pairs)
            user_emb, item_emb = model(A_norm)
            scores = item_emb @ user_emb[u_idx]
    except Exception as e:
        print(f"LightGCN: error en inferencia: {e}")
        return recomendar_popularidad(usuario_id, top_n=top_n)

    k = min(top_n, num_items)
    if k <= 0:
        return recomendar_popularidad(usuario_id, top_n=top_n)

    top_indices = torch.topk(scores, k=k).indices.numpy()
    inv = {v: k for k, v in item_index.items()}
    return [(inv[idx], float(scores[idx])) for idx in top_indices]
