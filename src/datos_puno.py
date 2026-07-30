# src/datos_puno.py
import pandas as pd
import networkx as nx
import os
import csv
from math import radians, sin, cos, sqrt, atan2   # <-- nuevo import para Haversine

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

# Coordenadas curadas a mano — NUNCA se pisan con lo que venga del catálogo OSM.
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
    # Atractivos reales del CSV que pueden faltar
    "Aramu Muru": [-15.733, -69.950],
    "Cutimbo": [-15.683, -70.117],
    "Pukara": [-15.250, -70.367],
    # Alias para el CSV real que usa "Islas Uros" (sin "de los")
    "Islas Uros": [-15.823, -69.963],
}

# Categoría de cada uno de los 13 lugares curados a mano (para colorear capas del mapa
# y para la heurística marítima). Se usa un vocabulario compatible con las categorías
# del catálogo OSM (Isla, Lago, Mirador, Museo, Sitio Arqueológico, Religioso, Evento,
# Senderismo, Naturaleza, Hotel).
categorias_atractivos = {
    "Lago Titicaca": "Lago",
    "Islas de los Uros": "Isla",
    "Isla Taquile": "Isla",
    "Sillustani": "Sitio Arqueológico",
    "Catedral de Puno": "Religioso",
    "Mirador El Condor": "Mirador",
    "Ruta del Qhapaq Ñan": "Senderismo",
    "Museo Carlos Dreyer": "Museo",
    "Chucuito": "Sitio Arqueológico",
    "Festividad Virgen de la Candelaria": "Evento",
    "Aramu Muru": "Sitio Arqueológico",
    "Cutimbo": "Sitio Arqueológico",
    "Pukara": "Sitio Arqueológico",
    "Islas Uros": "Isla",
}

# ==============================================
# 1.5 CATÁLOGO EXTENDIDO DESDE OSM (lugares_puno_osm.csv)
# ==============================================
RUTA_CATALOGO_OSM = os.path.join('datos', 'lugares_puno_osm.csv')


def cargar_catalogo_osm(ruta_csv=RUTA_CATALOGO_OSM):
    """
    Lee el catálogo de ~400 lugares extraído de OSM (nombre, categoria, latitud, longitud).

    Devuelve una lista de dicts [{nombre, categoria, lat, lon}, ...] o [] si el archivo
    no existe / no se puede leer. Se prueba primero utf-8 (el formato correcto del
    archivo) y sólo si falla se cae a latin-1, por si el CSV viniera de un pipeline
    con problemas de encoding como el que generó los signos de interrogación en otro
    archivo del proyecto.
    """
    if not os.path.exists(ruta_csv):
        print(f"[catalogo_osm] No se encontró {ruta_csv}. Se omite la carga del catálogo.")
        return []

    df_osm = None
    for encoding in ("utf-8", "latin-1"):
        try:
            df_osm = pd.read_csv(ruta_csv, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"[catalogo_osm] Error leyendo {ruta_csv} con encoding={encoding}: {e}")
            return []

    if df_osm is None:
        print(f"[catalogo_osm] No se pudo decodificar {ruta_csv} con utf-8 ni latin-1.")
        return []

    columnas_esperadas = {"nombre", "categoria", "latitud", "longitud"}
    if not columnas_esperadas.issubset(set(df_osm.columns)):
        print(f"[catalogo_osm] Faltan columnas esperadas. Columnas encontradas: {list(df_osm.columns)}")
        return []

    # Aviso defensivo: si aparecen signos de interrogación sueltos en nombre/categoria,
    # probablemente el archivo esté corrupto por un problema de encoding en origen.
    sospechosos = df_osm["nombre"].astype(str).str.contains(r"\?", regex=True).sum()
    if sospechosos > 0:
        print(f"[catalogo_osm] Aviso: {sospechosos} filas con '?' en 'nombre' — posible corrupción de encoding en el CSV de origen.")

    df_osm = df_osm.dropna(subset=["nombre", "latitud", "longitud"])
    df_osm = df_osm.drop_duplicates(subset=["nombre"], keep="first")

    catalogo = []
    for _, fila in df_osm.iterrows():
        try:
            catalogo.append({
                "nombre": str(fila["nombre"]).strip(),
                "categoria": str(fila["categoria"]).strip() if pd.notna(fila["categoria"]) else "Otro",
                "lat": float(fila["latitud"]),
                "lon": float(fila["longitud"]),
            })
        except (ValueError, TypeError):
            continue

    print(f"[catalogo_osm] Catálogo OSM cargado: {len(catalogo)} lugares válidos desde {ruta_csv}.")
    return catalogo


def completar_coordenadas_con_catalogo(catalogo):
    """
    Agrega a `coordenadas_atractivos` / `categorias_atractivos` todos los lugares del
    catálogo cuyo nombre (comparado sin distinguir mayúsculas/acentos de espacios) NO
    exista ya entre los curados a mano. Los 13 manuales quedan intactos siempre.
    """
    existentes_lower = {nombre.strip().lower() for nombre in coordenadas_atractivos}
    agregados = 0
    ya_existian = 0

    for lugar in catalogo:
        clave = lugar["nombre"].strip().lower()
        if clave in existentes_lower:
            ya_existian += 1
            continue
        coordenadas_atractivos[lugar["nombre"]] = [lugar["lat"], lugar["lon"]]
        categorias_atractivos[lugar["nombre"]] = lugar["categoria"]
        existentes_lower.add(clave)
        agregados += 1

    print(f"[catalogo_osm] {agregados} lugares nuevos incorporados, {ya_existian} ya existían (no se pisaron).")
    print(f"[catalogo_osm] Total de lugares con coordenadas: {len(coordenadas_atractivos)}.")


_catalogo_osm = cargar_catalogo_osm()
if _catalogo_osm:
    completar_coordenadas_con_catalogo(_catalogo_osm)

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

    col_usuario = 'nacionalidad'
    col_atractivo = 'sitio_turistico'
    col_visitantes = 'num_visitantes'
    col_satisfaccion = 'satisfaccion_1_5'

    if col_usuario not in df.columns or col_atractivo not in df.columns:
        print(f"ERROR: No se encontraron las columnas '{col_usuario}' o '{col_atractivo}'.")
        return None, None, None

    grouped = df.groupby([col_usuario, col_atractivo]).agg(
        total_visitantes=(col_visitantes, 'sum'),
        satisfaccion_promedio=(col_satisfaccion, 'mean')
    ).reset_index()
    grouped = grouped.rename(columns={col_usuario: 'usuario', col_atractivo: 'atractivo'})

    usuarios_reales = grouped['usuario'].dropna().unique().tolist()
    atractivos_reales = grouped['atractivo'].dropna().unique().tolist()

    print(f"Usuarios reales: {len(usuarios_reales)} (primeros 5: {usuarios_reales[:5]})")
    print(f"Atractivos reales: {len(atractivos_reales)} (primeros 5: {atractivos_reales[:5]})")

    user_map = {u: f"U{i}" for i, u in enumerate(usuarios_reales)}
    poi_map = {p: f"POI{i}" for i, p in enumerate(atractivos_reales)}

    G = nx.Graph()
    for u in usuarios_reales:
        G.add_node(user_map[u], tipo='usuario', nombre=u)
    for p in atractivos_reales:
        coords = coordenadas_atractivos.get(p, [None, None])
        G.add_node(poi_map[p], tipo='atractivo', nombre=p, 
                   tipo_atractivo='', zona='', lat=coords[0], lon=coords[1])

    for _, row in grouped.iterrows():
        u_id = user_map[row['usuario']]
        p_id = poi_map[row['atractivo']]
        peso = row['total_visitantes'] * row['satisfaccion_promedio']
        if G.has_edge(u_id, p_id):
            G[u_id][p_id]['peso'] += peso
        else:
            G.add_edge(u_id, p_id, relacion='visito', peso=peso)

    print(f"Grafo real construido: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas.")

    usuarios = [{'id': user_map[u], 'nombre': u, 'preferencias': []} for u in usuarios_reales]
    atractivos = [{'id': poi_map[p], 'nombre': p, 'tipo': '', 'zona': ''} for p in atractivos_reales]

    # Satisfacción promedio agregada por atractivo (independiente del usuario), útil
    # para mostrar un "rating" real en las tarjetas de recomendación.
    satisfaccion_por_atractivo = (
        df.groupby(col_atractivo)[col_satisfaccion].mean().to_dict()
    )
    global _SATISFACCION_REAL_POR_NOMBRE
    _SATISFACCION_REAL_POR_NOMBRE = {
        str(k): float(v) for k, v in satisfaccion_por_atractivo.items() if pd.notna(v)
    }

    return G, usuarios, atractivos

# Satisfacción real (1-5) por nombre de sitio, poblada por cargar_datos_reales() si el
# CSV está disponible. Si queda vacío, obtener_rating() cae a una estimación
# determinística por nombre.
_SATISFACCION_REAL_POR_NOMBRE = {}

# ==============================================
# 3. FUNCIONES PARA USUARIOS E INTERACCIONES EXTRA
# ==============================================
ARCHIVO_USUARIOS_EXTRA = "datos/usuarios_extra.csv"
ARCHIVO_INTERACCIONES_EXTRA = "datos/interacciones_extra.csv"


def _reparar_csv_usuarios():
    """Repara usuarios_extra.csv si tiene cabecera corrupta (un solo paso)."""
    if not os.path.exists(ARCHIVO_USUARIOS_EXTRA):
        return
    try:
        raw = open(ARCHIVO_USUARIOS_EXTRA, "r", encoding="utf-8", errors="replace").readlines()
    except Exception:
        return
    if not raw:
        return
    header = raw[0].strip().lower()
    if "id" in header and "nombre" in header:
        return  # ya está sano

    # intentar reconstruir: la primera línea es en realidad datos,
    # el header correcto es id,nombre,preferencias,edad
    registros = []
    for linea in raw:
        linea = linea.strip()
        if not linea:
            continue
        partes = csv.reader([linea]).__next__()
        # si la línea tiene 3-4 campos, es formato simple sin cabecera
        if len(partes) >= 3:
            try:
                lid = partes[0]
                lnombre = partes[1]
                lprefs = partes[2] if len(partes) > 2 else ""
                ledad = partes[3] if len(partes) > 3 else ""
                registros.append({"id": lid, "nombre": lnombre, "preferencias": lprefs, "edad": ledad})
            except Exception:
                continue

    if not registros:
        return
    pd.DataFrame(registros).to_csv(ARCHIVO_USUARIOS_EXTRA, index=False)
    print(f"[datos_puno] usuarios_extra.csv reparado: {len(registros)} registros.")


def _reparar_csv_interacciones():
    """Repara interacciones_extra.csv si falta cabecera."""
    if not os.path.exists(ARCHIVO_INTERACCIONES_EXTRA):
        return
    try:
        raw = open(ARCHIVO_INTERACCIONES_EXTRA, "r", encoding="utf-8", errors="replace").read()
    except Exception:
        return
    if not raw.strip():
        return
    if raw.startswith("usuario_id"):
        return  # ya está sano
    try:
        df = pd.read_csv(ARCHIVO_INTERACCIONES_EXTRA, header=None,
                         names=["usuario_id", "atractivo_id", "peso"])
        df.to_csv(ARCHIVO_INTERACCIONES_EXTRA, index=False)
        print(f"[datos_puno] interacciones_extra.csv reparado: {len(df)} registros.")
    except Exception:
        return


def cargar_usuarios_extra():
    _reparar_csv_usuarios()
    if not os.path.exists(ARCHIVO_USUARIOS_EXTRA):
        return []
    try:
        df = pd.read_csv(ARCHIVO_USUARIOS_EXTRA)
        if 'id' not in df.columns or 'nombre' not in df.columns:
            return []
        # limpiar NaN en campos clave
        df = df.dropna(subset=["id", "nombre"])
        return df.to_dict('records')
    except Exception as e:
        print(f"Error al leer {ARCHIVO_USUARIOS_EXTRA}: {e}")
        return []

def cargar_interacciones_extra():
    _reparar_csv_interacciones()
    if not os.path.exists(ARCHIVO_INTERACCIONES_EXTRA):
        return []
    try:
        df = pd.read_csv(ARCHIVO_INTERACCIONES_EXTRA)
        if 'usuario_id' not in df.columns or 'atractivo_id' not in df.columns:
            return []
        return df.to_dict('records')
    except Exception as e:
        print(f"Error al leer {ARCHIVO_INTERACCIONES_EXTRA}: {e}")
        return []

def guardar_nuevo_usuario(nombre, preferencias_lista, edad=None):
    """
    Registra un nuevo turista. `edad` es opcional (puede venir None si el formulario
    no la pide) y se usa luego por `reordenar_por_edad` como señal adicional de
    recomendación (sin tocar los motores RWR/LightGCN/Meta).

    Usa pandas para leer+escribir el CSV completo en vez de solo hacer append, para
    migrar de forma segura archivos viejos que no tenían la columna 'edad'.
    """
    os.makedirs('datos', exist_ok=True)
    usuarios_extra = cargar_usuarios_extra()
    max_id = 0
    for u in usuarios_extra:
        try:
            if 'id' in u:
                max_id = max(max_id, int(u['id']))
        except Exception:
            pass
    nuevo_id = max_id + 1

    nueva_fila = {
        'id': nuevo_id,
        'nombre': nombre,
        'preferencias': ','.join(preferencias_lista),
        'edad': edad if edad is not None else '',
    }
    if os.path.exists(ARCHIVO_USUARIOS_EXTRA):
        df_existente = pd.read_csv(ARCHIVO_USUARIOS_EXTRA)
        for col in ['id', 'nombre', 'preferencias', 'edad']:
            if col not in df_existente.columns:
                df_existente[col] = ''
        df_final = pd.concat([df_existente, pd.DataFrame([nueva_fila])], ignore_index=True)
    else:
        df_final = pd.DataFrame([nueva_fila])
    df_final.to_csv(ARCHIVO_USUARIOS_EXTRA, index=False)

    uid = f"EXT_{nuevo_id}"
    G_hibrido.add_node(uid, tipo='usuario', nombre=nombre, preferencias=preferencias_lista, edad=edad)
    usuarios.append({"id": uid, "nombre": nombre, "preferencias": preferencias_lista, "edad": edad})
    for a in atractivos:
        if a.get('tipo') in preferencias_lista:
            G_hibrido.add_edge(uid, a['id'], relacion='prefiere', peso=1.0)
    print(f"Usuario {nombre} agregado correctamente con ID {uid} (edad={edad})")
    return uid

def registrar_visita(usuario_id, atractivo_id, peso=1.0):
    os.makedirs('datos', exist_ok=True)
    file_exists = os.path.exists(ARCHIVO_INTERACCIONES_EXTRA)
    with open(ARCHIVO_INTERACCIONES_EXTRA, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['usuario_id', 'atractivo_id', 'peso'])
        writer.writerow([usuario_id, atractivo_id, peso])
    if G_hibrido.has_edge(usuario_id, atractivo_id):
        G_hibrido[usuario_id][atractivo_id]['peso'] += peso
    else:
        G_hibrido.add_edge(usuario_id, atractivo_id, relacion='visito', peso=peso)
    print(f"Visita registrada: {usuario_id} -> {atractivo_id} (+{peso})")

# ==============================================
# 4. CARGA PRINCIPAL (REAL + EXTRA)
# ==============================================
G_hibrido = None
usuarios = None
atractivos = None

_NORM_TIPO = {
    "sitio arqueológico": "arqueológico",
    "sitio arqueologico": "arqueológico",
    "iglesia": "religioso",
    "capilla": "religioso",
    "catédral": "religioso",
    "catedral": "religioso",
    "arqueologico": "arqueológico",
}


def _construir_sistema():
    """Construye/inicializa G_hibrido, usuarios, atractivos desde CSVs.
    Puede llamarse varias veces (recarga) mutando en los mismos objetos
    para que las referencias de otros módulos sigan siendo válidas."""
    global G_hibrido, usuarios, atractivos

    # Primera vez: crear objetos nuevos
    if G_hibrido is None:
        G_hibrido = nx.Graph()
        usuarios = []
        atractivos = []

    # Limpiar para recarga
    G_hibrido.clear()
    usuarios.clear()
    atractivos.clear()

    G_real, usuarios_real, atractivos_real = cargar_datos_reales()

    if G_real is not None:
        print("Usando datos REALES del CSV + atractivos sintéticos.")
        # Copiar nodos de G_real a G_hibrido
        for n, attrs in G_real.nodes(data=True):
            G_hibrido.add_node(n, **attrs)
        for u, v, attrs in G_real.edges(data=True):
            G_hibrido.add_edge(u, v, **attrs)
        usuarios.extend(usuarios_real)
        atractivos.extend(atractivos_real)
    else:
        print("Usando datos SINTÉTICOS (fallback).")
        for u in usuarios_sinteticos:
            G_hibrido.add_node(u["id"], tipo="usuario", nombre=u["nombre"],
                               preferencias=u["preferencias"])
        for a in atractivos_sinteticos:
            G_hibrido.add_node(a["id"], tipo="atractivo", nombre=a["nombre"],
                               tipo_atractivo=a["tipo"], zona=a["zona"])
        for u in usuarios_sinteticos:
            for a in atractivos_sinteticos:
                if a["tipo"] in u["preferencias"]:
                    G_hibrido.add_edge(u["id"], a["id"], relacion="prefiere", peso=1.0)
                if a["zona"].lower() in [p.lower() for p in u["preferencias"]]:
                    G_hibrido.add_edge(u["id"], a["id"], relacion="interes_zona", peso=0.8)
        usuarios.extend(usuarios_sinteticos)
        atractivos.extend(atractivos_sinteticos)

    # Enriquecer con atractivos sintéticos siempre
    for a in atractivos_sinteticos:
        if a["id"] not in G_hibrido:
            G_hibrido.add_node(a["id"], tipo="atractivo", nombre=a["nombre"],
                               tipo_atractivo=a["tipo"], zona=a["zona"])
            if a not in atractivos:
                atractivos.append(a)

    # Asignar tipo_atractivo a nodos reales según categorias_atractivos
    _lookup_categoria = {}
    for _nombre, _cat in categorias_atractivos.items():
        _clave = _nombre.strip().lower()
        _lookup_categoria[_clave] = _cat
        _simplificada = _clave.replace(" de ", " ").replace(" los ", " ").replace(" las ", " ").replace(" del ", " ").replace(" la ", " ").replace(" el ", " ")
        if _simplificada != _clave:
            _lookup_categoria[_simplificada] = _cat

    for n, attrs in list(G_hibrido.nodes(data=True)):
        if attrs.get("tipo") == "atractivo" and not attrs.get("tipo_atractivo"):
            nombre = attrs.get("nombre", "")
            _clave = nombre.strip().lower()
            _simplificada = _clave.replace(" de ", " ").replace(" los ", " ").replace(" las ", " ").replace(" del ", " ").replace(" la ", " ").replace(" el ", " ")
            _cat = _lookup_categoria.get(_clave) or _lookup_categoria.get(_simplificada) or ""
            cat = str(_cat).strip().lower()
            if cat:
                G_hibrido.nodes[n]["tipo_atractivo"] = cat
                for a in atractivos:
                    if a["id"] == n:
                        a["tipo"] = cat
                        break

    # Aristas de similitud entre atractivos
    _norm_tipo = lambda t: _NORM_TIPO.get(t, t)
    nombres_attr = [n for n, attrs in G_hibrido.nodes(data=True) if attrs.get("tipo") == "atractivo"]
    for i, a1_id in enumerate(nombres_attr):
        for a2_id in nombres_attr[i+1:]:
            if G_hibrido.has_edge(a1_id, a2_id):
                continue
            tipo1 = _norm_tipo(str(G_hibrido.nodes[a1_id].get("tipo_atractivo", "")).lower().strip())
            tipo2 = _norm_tipo(str(G_hibrido.nodes[a2_id].get("tipo_atractivo", "")).lower().strip())
            zona1 = str(G_hibrido.nodes[a1_id].get("zona", "")).lower().strip()
            zona2 = str(G_hibrido.nodes[a2_id].get("zona", "")).lower().strip()
            peso = 0.0
            if tipo1 and tipo1 == tipo2:
                peso = 0.9
            elif zona1 and zona1 == zona2:
                peso = 0.6
            if peso > 0:
                G_hibrido.add_edge(a1_id, a2_id, relacion="similar", peso=peso)

    print(f"Atractivos en grafo: {len([n for n in G_hibrido.nodes if G_hibrido.nodes[n].get('tipo') == 'atractivo'])}")
    print(f"Usuarios en grafo: {len([n for n in G_hibrido.nodes if G_hibrido.nodes[n].get('tipo') == 'usuario'])}")

    # Cargar usuarios extra
    for u_extra in cargar_usuarios_extra():
        try:
            if 'id' not in u_extra or 'nombre' not in u_extra:
                continue
            uid = f"EXT_{u_extra['id']}"
            prefs_str = u_extra.get('preferencias', '')
            prefs = prefs_str.split(',') if isinstance(prefs_str, str) and prefs_str else []
            edad_raw = u_extra.get('edad')
            edad = None
            try:
                if edad_raw not in (None, '') and not (isinstance(edad_raw, float) and pd.isna(edad_raw)):
                    edad = int(float(edad_raw))
            except (ValueError, TypeError):
                edad = None
            if uid not in G_hibrido:
                G_hibrido.add_node(uid, tipo='usuario', nombre=u_extra['nombre'], preferencias=prefs, edad=edad)
                usuarios.append({"id": uid, "nombre": u_extra['nombre'], "preferencias": prefs, "edad": edad})
                for a in atractivos:
                    if a.get('tipo') in prefs:
                        G_hibrido.add_edge(uid, a['id'], relacion='prefiere', peso=1.0)
        except Exception as e:
            print(f"Error al cargar usuario extra: {e}")

    # Cargar interacciones extra
    for inter in cargar_interacciones_extra():
        try:
            uid = inter.get('usuario_id')
            aid = inter.get('atractivo_id')
            peso = inter.get('peso', 1.0)
            if uid and aid and uid in G_hibrido and aid in G_hibrido:
                if G_hibrido.has_edge(uid, aid):
                    G_hibrido[uid][aid]['peso'] += peso
                else:
                    G_hibrido.add_edge(uid, aid, relacion='visito', peso=peso)
        except Exception as e:
            print(f"Error al cargar interacción extra: {e}")

    print(f"Grafo final: {G_hibrido.number_of_nodes()} nodos, {G_hibrido.number_of_edges()} aristas.")


def recargar_datos():
    """Reconstruye G_hibrido, usuarios, atractivos desde cero
    (relee CSVs). Útil tras agregar nuevos datos."""
    _construir_sistema()


# Construir en import
_construir_sistema()

# ==============================================
# 5. GRAFO DE RUTAS Y ALGORITMO A* (CON HEURÍSTICA MARÍTIMA)
# ==============================================

def haversine(lat1, lon1, lat2, lon2):
    """Distancia en kilómetros entre dos puntos geográficos (fórmula del Haversine)."""
    R = 6371  # Radio de la Tierra en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


# Categorías que representan un punto solo alcanzable cruzando el lago (isla) o que
# son el propio lago. Cualquier arista donde participe uno de estos puntos representa,
# como mínimo, un tramo de lancha/bote en lugar de un tramo por tierra/carretera.
CATEGORIAS_MARITIMAS = {"isla", "lago"}

# Factor de penalización: una lancha en el Titicaca avanza mucho más lento que un
# vehículo por carretera (~8-15 km/h en lancha turística vs ~50-60 km/h en auto), y
# además suele exigir trasbordo/espera. Usamos un factor conservador para que el A*
# prefiera rutas por tierra cuando existan, y sólo "cruce" el lago cuando el destino
# lo requiere de verdad (p. ej. llegar a una isla).
FACTOR_MARITIMO = 3.0


def requiere_cruce_lacustre(nombre):
    categoria = categorias_atractivos.get(nombre, "")
    return categoria.strip().lower() in CATEGORIAS_MARITIMAS


def construir_grafo_rutas():
    """
    Construye un grafo completo entre todos los atractivos con coordenadas.
    El peso de cada arista es la distancia Haversine (km), multiplicada por
    FACTOR_MARITIMO si el origen o el destino requieren cruce lacustre (heurística
    marítima), para reflejar que ese tramo no se recorre por carretera.
    """
    G_rutas = nx.Graph()
    nombres = list(coordenadas_atractivos.keys())

    for nombre in nombres:
        lat, lon = coordenadas_atractivos[nombre]
        if lat is None or lon is None:
            continue
        G_rutas.add_node(
            nombre, lat=lat, lon=lon,
            categoria=categorias_atractivos.get(nombre, "Otro"),
        )

    nodos_validos = list(G_rutas.nodes)
    for i, nombre1 in enumerate(nodos_validos):
        lat1, lon1 = G_rutas.nodes[nombre1]['lat'], G_rutas.nodes[nombre1]['lon']
        for nombre2 in nodos_validos[i + 1:]:
            lat2, lon2 = G_rutas.nodes[nombre2]['lat'], G_rutas.nodes[nombre2]['lon']
            distancia = haversine(lat1, lon1, lat2, lon2)
            maritimo = requiere_cruce_lacustre(nombre1) or requiere_cruce_lacustre(nombre2)
            peso = distancia * FACTOR_MARITIMO if maritimo else distancia
            G_rutas.add_edge(
                nombre1, nombre2,
                weight=peso, distancia_km=distancia, maritimo=maritimo,
            )
    return G_rutas

G_rutas = construir_grafo_rutas()
print(f"Grafo de rutas creado: {G_rutas.number_of_nodes()} nodos, {G_rutas.number_of_edges()} aristas.")

# ==============================================
# 6. NAVEGACIÓN REALISTA: PUERTOS, CURVA MARÍTIMA Y RUTEO POR CARRETERA
# ==============================================
# Todo lo que sigue es puramente visual/geográfico (no toca los motores de
# recomendación). Se usa desde demo.py para dibujar el mapa de resultados con
# el mismo lenguaje visual que el sistema hermano de Puno: puerto de embarque
# + curva náutica para destinos que "requiere_cruce_lacustre", y ruteo real
# por carretera (con fallback a línea recta) para el resto.

import math

PUERTO_PUNO = (-15.8409, -70.0180)   # Muelle / puerto principal de Puno
PUNO_CENTRO = (-15.8402, -70.0219)   # Plaza de Armas de Puno

# Embarcaderos conocidos del lago Titicaca (lado peruano). Se usa el más cercano
# al destino marítimo para simular un trayecto realista: tierra hasta el puerto
# + agua desde el puerto hasta la isla/lago.
PUERTOS_TITICACA = [
    {"nombre": "Puerto de Puno", "coords": PUERTO_PUNO},
    {"nombre": "Puerto Chifrón / Capachica", "coords": (-15.6415, -69.8330)},
    {"nombre": "Puerto de Llachón", "coords": (-15.7165, -69.7850)},
    {"nombre": "Puerto de Ccotos", "coords": (-15.6055, -69.7770)},
    {"nombre": "Embarcadero de Juli", "coords": (-16.2100, -69.4620)},
]


def puerto_mas_conveniente(destino) -> dict:
    """Elige el embarcadero más cercano (Haversine) a un destino marítimo dado."""
    return min(
        PUERTOS_TITICACA,
        key=lambda p: haversine(p["coords"][0], p["coords"][1], destino[0], destino[1]),
    )


def ruta_curva_maritima(origen, destino, segmentos: int = 28):
    """
    Genera una curva de Bézier cuadrática suave entre `origen` y `destino`, para que
    el tramo lacustre se distinga visualmente de una carretera recta en el mapa.
    """
    lat1, lon1 = origen
    lat2, lon2 = destino
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    distancia = math.sqrt(dlat * dlat + dlon * dlon)
    if distancia < 1e-9:
        return [list(origen), list(destino)]

    # Offset perpendicular pequeño: da lectura de ruta náutica sin alejarla del lago.
    offset = min(0.045, distancia * 0.18)
    perp_lat = -dlon / distancia * offset
    perp_lon = dlat / distancia * offset
    control = ((lat1 + lat2) / 2 + perp_lat, (lon1 + lon2) / 2 + perp_lon)

    puntos = []
    for i in range(segmentos + 1):
        t = i / segmentos
        lat = (1 - t) ** 2 * lat1 + 2 * (1 - t) * t * control[0] + t ** 2 * lat2
        lon = (1 - t) ** 2 * lon1 + 2 * (1 - t) * t * control[1] + t ** 2 * lon2
        puntos.append([lat, lon])
    return puntos


def obtener_ruta_terrestre(origen, destino, timeout: int = 3):
    """
    Consulta el servicio público OSRM para obtener la geometría real de una ruta por
    carretera entre dos puntos. Si el servicio no responde (sin red, timeout, error),
    devuelve None para que el llamador pueda caer a una línea recta aproximada.
    """
    try:
        import requests
        url = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{origen[1]},{origen[0]};{destino[1]},{destino[0]}?overview=full&geometries=geojson"
        )
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            if data.get("routes"):
                coords = data["routes"][0]["geometry"]["coordinates"]
                return [[lat, lon] for lon, lat in coords]
    except Exception:
        pass
    return None


# Rutas aproximadas (sin OSRM) hacia puertos secundarios. Se usan como
# fallback cuando obtener_ruta_terrestre() no responde (sin internet o
# timeout), para evitar la línea recta genérica.
RUTAS_APROX_PUERTOS = {
    "Puerto Chifrón / Capachica": [
        PUERTO_PUNO,
        (-15.7630, -70.0040),
        (-15.7050, -69.9600),
        (-15.6650, -69.9000),
        (-15.6415, -69.8330),
    ],
    "Puerto de Llachón": [
        PUERTO_PUNO,
        (-15.7630, -70.0040),
        (-15.7050, -69.9600),
        (-15.6650, -69.9000),
        (-15.6660, -69.8400),
        (-15.7165, -69.7850),
    ],
    "Puerto de Ccotos": [
        PUERTO_PUNO,
        (-15.7630, -70.0040),
        (-15.7050, -69.9600),
        (-15.6650, -69.9000),
        (-15.6250, -69.8350),
        (-15.6055, -69.7770),
    ],
    "Embarcadero de Juli": [
        PUERTO_PUNO,
        (-15.8800, -69.9700),
        (-15.9650, -69.8450),
        (-16.0800, -69.6500),
        (-16.2100, -69.4620),
    ],
}


def ruta_terrestre_hacia_puerto(nombre_puerto: str, coords_puerto):
    """Tramo terrestre desde el Puerto de Puno hasta el embarcadero elegido."""
    ruta = obtener_ruta_terrestre(PUERTO_PUNO, coords_puerto)
    if ruta:
        return ruta
    aprox = RUTAS_APROX_PUERTOS.get(nombre_puerto)
    if aprox:
        return [list(p) for p in aprox]
    return [list(PUERTO_PUNO), list(coords_puerto)]


# ------------------------------------------------------------------
# Aeropuertos del Perú (para selector de origen + ruta aérea en el mapa)
# ------------------------------------------------------------------

RUTA_AEROPUERTOS = os.path.join('datos', 'aeropuertos_peru.csv')


def cargar_aeropuertos(ruta_csv=RUTA_AEROPUERTOS):
    """
    Lee aeropuertos_peru.csv y devuelve:
      aeropuertos : dict {nombre: {"ciudad": str, "coords": (lat, lon)}}
      hub_coords  : (lat, lon) del aeropuerto marcado como hub Juliaca, o None
      hub_nombre  : str nombre del hub, o None
    """
    if not os.path.exists(ruta_csv):
        print(f"[aeropuertos] No se encontró {ruta_csv}.")
        return {}, None, None

    import pandas as pd
    df = pd.read_csv(ruta_csv)
    requeridas = {"nombre", "ciudad", "latitud", "longitud"}
    if not requeridas.issubset(set(df.columns)):
        print(f"[aeropuertos] Faltan columnas. Encontradas: {list(df.columns)}")
        return {}, None, None

    aeropuertos = {}
    hub_coords = None
    hub_nombre = None

    for _, fila in df.iterrows():
        nombre = str(fila["nombre"]).strip()
        coords = (float(fila["latitud"]), float(fila["longitud"]))
        aeropuertos[nombre] = {
            "ciudad": str(fila.get("ciudad", "")).strip(),
            "coords": coords,
        }
        es_hub = str(fila.get("es_hub_juliaca", "0")).strip().lower()
        if es_hub in ("1", "true", "sí", "si", "yes"):
            hub_coords = coords
            hub_nombre = nombre

    return aeropuertos, hub_coords, hub_nombre


AEROPUERTOS_PERU, JULIACA_AIRPORT_COORDS, JULIACA_AIRPORT_NOMBRE = cargar_aeropuertos()


# ------------------------------------------------------------------
# Rating y descripción para las tarjetas de resultado
# ------------------------------------------------------------------
# Si el CSV real tiene columna de satisfacción, usamos el promedio real por sitio
# (poblado en cargar_datos_reales -> _SATISFACCION_REAL_POR_NOMBRE). Si no hay dato
# real disponible para ese nombre, se calcula una estimación determinística a partir
# del propio nombre (siempre el mismo valor para el mismo lugar, sin azar en cada
# render) para que las tarjetas siempre muestren algo razonable.

_DESCRIPCIONES_POR_CATEGORIA = {
    "isla": "Isla del Lago Titicaca, accesible en lancha desde Puno, con paisajes y comunidades locales.",
    "lago": "Extensión del Lago Titicaca, el lago navegable más alto del mundo.",
    "sitio arqueológico": "Vestigios arqueológicos de las culturas preincaicas e incaicas de la región.",
    "religioso": "Templo o santuario de valor histórico y devoción popular en Puno.",
    "mirador": "Punto panorámico con vistas privilegiadas de la ciudad y el lago.",
    "museo": "Espacio cultural con piezas y colecciones representativas de la región.",
    "evento": "Festividad o celebración tradicional emblemática de la cultura puneña.",
    "senderismo": "Ruta o sendero para recorrer a pie el paisaje altiplánico.",
    "naturaleza": "Espacio natural de interés paisajístico en la región de Puno.",
    "hotel": "Alojamiento turístico ubicado en la región de Puno.",
}


def obtener_descripcion(nombre: str) -> str:
    categoria = str(categorias_atractivos.get(nombre, "Otro")).strip().lower()
    return _DESCRIPCIONES_POR_CATEGORIA.get(
        categoria, f"{nombre} es uno de los atractivos turísticos de la región de Puno."
    )


# ------------------------------------------------------------------
# Edad como señal adicional de recomendación
# ------------------------------------------------------------------
# No se re-entrena ningún motor: se reordena el ranking ya calculado (RWR,
# LightGCN o Meta) aplicando un factor multiplicativo por categoría según
# rangos de edad típicos, y se vuelve a ordenar por el score ajustado.

def afinidad_categoria_por_edad(edad) -> dict:
    if edad is None:
        return {}
    try:
        edad = int(edad)
    except (ValueError, TypeError):
        return {}

    if edad < 25:
        return {"isla": 1.15, "lago": 1.15, "senderismo": 1.20, "evento": 1.15,
                "museo": 0.90, "religioso": 0.90}
    elif edad < 45:
        return {"isla": 1.05, "mirador": 1.10, "sitio arqueológico": 1.05}
    elif edad < 65:
        return {"sitio arqueológico": 1.15, "religioso": 1.15, "museo": 1.15,
                "senderismo": 0.85}
    else:
        return {"museo": 1.20, "religioso": 1.20, "sitio arqueológico": 1.10,
                "senderismo": 0.75, "isla": 0.85}


def reordenar_por_edad(ranking: list, edad) -> list:
    """Reordena una lista [(id, score), ...] ya generada por cualquiera de los
    tres motores, aplicando un pequeño boost/penalización por categoría según
    la edad del turista. Si `edad` es None, devuelve el ranking sin cambios."""
    boosts = afinidad_categoria_por_edad(edad)
    if not boosts or not ranking:
        return ranking

    ajustado = []
    for aid, score in ranking:
        nombre = G_hibrido.nodes[aid].get("nombre") if aid in G_hibrido.nodes else None
        categoria = str(categorias_atractivos.get(nombre, "Otro")).strip().lower()
        factor = boosts.get(categoria, 1.0)
        ajustado.append((aid, score * factor))

    ajustado.sort(key=lambda x: x[1], reverse=True)
    return ajustado


def obtener_rating(nombre: str) -> float:
    """Rating 1-5 para mostrar en las tarjetas: usa satisfacción real del CSV si existe,
    y si no, una estimación determinística (misma entrada -> mismo rating siempre)."""
    if nombre in _SATISFACCION_REAL_POR_NOMBRE:
        return round(float(_SATISFACCION_REAL_POR_NOMBRE[nombre]), 2)
    hash_nombre = sum(ord(c) for c in nombre)
    return round(3.5 + (hash_nombre % 150) / 100, 2)  # rango aprox. 3.5 - 5.0