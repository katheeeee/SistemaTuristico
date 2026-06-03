# datos_puno.py
import pandas as pd
import networkx as nx
import os

# ==============================================
# 1. DATOS SINTÉTICOS (FALLBACK)
# ==============================================
atractivos_sinteticos = [
    {"id": "A1", "nombre": "Lago Titicaca", "tipo": "lago", "zona": "Acuático", "popularidad": 10},
    {"id": "A2", "nombre": "Islas de los Uros", "tipo": "isla", "zona": "Lago", "popularidad": 10},
    {"id": "A3", "nombre": "Isla Taquile", "tipo": "isla", "zona": "Lago", "popularidad": 9},
    {"id": "A4", "nombre": "Sillustani", "tipo": "arqueológico", "zona": "Norte", "popularidad": 8},
    {"id": "A5", "nombre": "Catedral de Puno", "tipo": "religioso", "zona": "Centro", "popularidad": 7},
    {"id": "A6", "nombre": "Mirador El Condor", "tipo": "mirador", "zona": "Altura", "popularidad": 7},
    {"id": "A7", "nombre": "Museo Carlos Dreyer", "tipo": "museo", "zona": "Centro", "popularidad": 6},
    {"id": "A8", "nombre": "Chucuito", "tipo": "arqueológico", "zona": "Sur", "popularidad": 6},
    {"id": "A9", "nombre": "Festividad Virgen de la Candelaria", "tipo": "evento", "zona": "Puno", "popularidad": 9},
    {"id": "A10", "nombre": "Ruta del Qhapaq Ñan", "tipo": "senderismo", "zona": "Andes", "popularidad": 7},
]

usuarios_sinteticos = [
    {"id": "U1", "nombre": "Laura", "preferencias": ["lago", "isla", "naturaleza"]},
    {"id": "U2", "nombre": "Carlos", "preferencias": ["arqueológico", "museo", "historia"]},
    {"id": "U3", "nombre": "Marta", "preferencias": ["evento", "religioso", "cultura"]},
    {"id": "U4", "nombre": "Jorge", "preferencias": ["senderismo", "mirador", "aventura"]},
]

coordenadas_atractivos = {
    "Lago Titicaca": [-15.840, -69.400],
    "Islas de los Uros": [-15.823, -69.963],
    "Isla Taquile": [-15.774, -69.684],
    "Sillustani": [-15.716, -70.148],
    "Catedral de Puno": [-15.839, -70.027],
    "Mirador El Condor": [-15.850, -70.030],
    "Ruta del Qhapaq Ñan": [-15.800, -70.000],
    "Museo Carlos Dreyer": [-15.840, -70.027],
    "Chucuito": [-15.883, -69.900],
    "Festividad Virgen de la Candelaria": [-15.840, -70.027],
}

# ==============================================
# 2. FUNCIÓN PARA CARGAR DATOS REALES (CSV)
# ==============================================
def cargar_datos_reales():
    ruta_csv = os.path.join('datos', 'turismo_puno_2019_2024.csv')
    if not os.path.exists(ruta_csv):
        print(f"No se encontró el archivo {ruta_csv}. Usando datos sintéticos.")
        return None, None, None

    try:
        df = pd.read_csv(ruta_csv)
        print(f"Archivo CSV cargado correctamente desde {ruta_csv}")
        print(f"Columnas disponibles: {list(df.columns)}")
    except Exception as e:
        print(f"Error al leer CSV: {e}")
        return None, None, None

    # --- NOMBRES REALES DE COLUMNAS ---
    col_usuario = 'nacionalidad'      # columna que identifica al turista
    col_atractivo = 'sitio_turistico' # columna que identifica el lugar
    # Columnas adicionales que podemos usar para peso o preferencia
    col_visitantes = 'num_visitantes'
    col_satisfaccion = 'satisfaccion_1_5'

    if col_usuario not in df.columns or col_atractivo not in df.columns:
        print(f"ERROR: No se encontraron las columnas '{col_usuario}' o '{col_atractivo}'.")
        print("Verifica los nombres en el CSV y ajusta el código.")
        return None, None, None

    # Agrupar por usuario y atractivo para sumar visitantes y promediar satisfacción
    grouped = df.groupby([col_usuario, col_atractivo]).agg(
        total_visitantes=(col_visitantes, 'sum'),
        satisfaccion_promedio=(col_satisfaccion, 'mean')
    ).reset_index()

    # Renombrar columnas para claridad
    grouped = grouped.rename(columns={col_usuario: 'usuario', col_atractivo: 'atractivo'})

    # Obtener listas únicas
    usuarios_reales = grouped['usuario'].dropna().unique().tolist()
    atractivos_reales = grouped['atractivo'].dropna().unique().tolist()

    print(f"Usuarios reales: {len(usuarios_reales)} (primeros 5: {usuarios_reales[:5]})")
    print(f"Atractivos reales: {len(atractivos_reales)} (primeros 5: {atractivos_reales[:5]})")

    # Crear mapeos a IDs internos
    user_map = {u: f"U{i}" for i, u in enumerate(usuarios_reales)}
    poi_map = {p: f"POI{i}" for i, p in enumerate(atractivos_reales)}

    # Construir grafo
    G = nx.Graph()
    for u in usuarios_reales:
        G.add_node(user_map[u], tipo='usuario', nombre=u)
    for p in atractivos_reales:
        # Buscar coordenadas para el atractivo (si existe)
        coords = coordenadas_atractivos.get(p, [None, None])
        G.add_node(poi_map[p], tipo='atractivo', nombre=p, 
                   tipo_atractivo='', zona='', lat=coords[0], lon=coords[1])

    # Agregar aristas con peso basado en total_visitantes y satisfacción
    for _, row in grouped.iterrows():
        u_id = user_map[row['usuario']]
        p_id = poi_map[row['atractivo']]
        # Peso combinado: visitantes * satisfacción (normalizado después si se desea)
        peso = row['total_visitantes'] * row['satisfaccion_promedio']
        if G.has_edge(u_id, p_id):
            G[u_id][p_id]['peso'] += peso
        else:
            G.add_edge(u_id, p_id, relacion='visito', peso=peso)

    print(f"Grafo real construido: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas.")

    # Crear estructuras compatibles con la demo
    # Para usuarios reales, no tenemos preferencias predefinidas; las podemos inferir más adelante
    usuarios = [{'id': user_map[u], 'nombre': u, 'preferencias': []} for u in usuarios_reales]
    atractivos = [{'id': poi_map[p], 'nombre': p, 'tipo': '', 'zona': ''} for p in atractivos_reales]

    return G, usuarios, atractivos

# ==============================================
# 3. CARGA PRINCIPAL (REAL O FALLBACK)
# ==============================================
G_hibrido = None
usuarios = None
atractivos = None

# Intentar cargar datos reales
G_real, usuarios_real, atractivos_real = cargar_datos_reales()

if G_real is not None:
    G_hibrido = G_real
    usuarios = usuarios_real
    atractivos = atractivos_real
    print("Usando datos REALES del CSV.")
else:
    print("Usando datos SINTÉTICOS (fallback).")
    # Construir grafo sintético (igual que antes)
    G_hibrido = nx.Graph()
    for a in atractivos_sinteticos:
        G_hibrido.add_node(a["id"], tipo="atractivo", nombre=a["nombre"], 
                           tipo_atractivo=a["tipo"], zona=a["zona"])
    for u in usuarios_sinteticos:
        G_hibrido.add_node(u["id"], tipo="usuario", nombre=u["nombre"], 
                           preferencias=u["preferencias"])
    # Aristas colaborativas
    for u in usuarios_sinteticos:
        for a in atractivos_sinteticos:
            if a["tipo"] in u["preferencias"]:
                G_hibrido.add_edge(u["id"], a["id"], relacion="prefiere", peso=1.0, tipo_arista="colaborativa")
            if a["zona"].lower() in [p.lower() for p in u["preferencias"]]:
                G_hibrido.add_edge(u["id"], a["id"], relacion="interes_zona", peso=0.8, tipo_arista="colaborativa")
    # Aristas de contenido
    for i, a1 in enumerate(atractivos_sinteticos):
        for a2 in atractivos_sinteticos[i+1:]:
            peso = 0.0
            if a1["tipo"] == a2["tipo"]:
                peso = 0.9
            elif a1["zona"] == a2["zona"]:
                peso = 0.6
            if peso > 0:
                G_hibrido.add_edge(a1["id"], a2["id"], relacion="similar", peso=peso, tipo_arista="contenido")
    usuarios = usuarios_sinteticos
    atractivos = atractivos_sinteticos

print(f"Grafo final: {G_hibrido.number_of_nodes()} nodos, {G_hibrido.number_of_edges()} aristas.")