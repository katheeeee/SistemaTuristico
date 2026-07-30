import os
import sys
import folium
import networkx as nx
import streamlit as st
from streamlit_folium import st_folium

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from grafo_hibrido import G_hibrido
from recomendador import recomendar
from datos_puno import (
    usuarios, coordenadas_atractivos, categorias_atractivos,
    guardar_nuevo_usuario, registrar_visita, haversine, G_rutas,
    PUERTOS_TITICACA, PUERTO_PUNO, PUNO_CENTRO,
    puerto_mas_conveniente, ruta_curva_maritima, obtener_ruta_terrestre,
    ruta_terrestre_hacia_puerto, requiere_cruce_lacustre,
    obtener_rating, obtener_descripcion, reordenar_por_edad,
    AEROPUERTOS_PERU, JULIACA_AIRPORT_COORDS, JULIACA_AIRPORT_NOMBRE,
)
from meta_recomendador import recomendar_meta
from lightgcn_model import recomendar_lightgcn
import styles

st.set_page_config(
    page_title="Sistema de Recomendación Turística — Puno",
    page_icon="🌄",
    layout="wide",
)
st.markdown(styles.FONT_AWESOME_CDN, unsafe_allow_html=True)
st.markdown(styles.inyectar_css(), unsafe_allow_html=True)

TILES_OSCURO_URL = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
TILES_OSCURO_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'


def mapa_oscuro(location, zoom_start):
    return folium.Map(
        location=location, zoom_start=zoom_start,
        tiles=TILES_OSCURO_URL, attr=TILES_OSCURO_ATTR,
    )

# ==============================================
# CAPAS POR CATEGORÍA
# ==============================================

CATEGORIAS_VISIBLES_POR_DEFECTO = {
    "isla", "lago", "mirador", "museo", "sitio arqueológico",
    "religioso", "evento", "senderismo", "naturaleza",
}


def agregar_capas_por_categoria(mapa, coordenadas, categorias, destacados=None, radio_normal=4, radio_destacado=8):
    destacados = destacados or set()
    capas = {}

    for nombre, (lat, lon) in coordenadas.items():
        categoria = categorias.get(nombre, "Otro")
        categoria_low = str(categoria).strip().lower()
        _, color = styles.icono_y_color(categoria)

        if categoria_low not in capas:
            capas[categoria_low] = folium.FeatureGroup(
                name=f"{categoria} ({sum(1 for c in categorias.values() if str(c).strip().lower() == categoria_low)})",
                show=categoria_low in CATEGORIAS_VISIBLES_POR_DEFECTO,
            )

        es_destacado = nombre in destacados
        folium.CircleMarker(
            location=[lat, lon],
            radius=radio_destacado if es_destacado else radio_normal,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85 if es_destacado else 0.45,
            opacity=0.9 if es_destacado else 0.5,
            tooltip=f"{nombre} · {categoria}",
        ).add_to(capas[categoria_low])

    for capa in capas.values():
        capa.add_to(mapa)

    folium.LayerControl(collapsed=False).add_to(mapa)
    return mapa


# ==============================================
# MAPA DE RESULTADOS
# ==============================================

def crear_mapa_resultados(ranking: list, motor_nombre: str, aeropuerto_origen: dict = None) -> folium.Map:
    puntos_validos = [
        (aid, score) for aid, score in ranking
        if aid in G_hibrido.nodes and G_hibrido.nodes[aid].get("nombre") in coordenadas_atractivos
    ]

    if puntos_validos:
        lats = [coordenadas_atractivos[G_hibrido.nodes[aid]["nombre"]][0] for aid, _ in puntos_validos]
        lons = [coordenadas_atractivos[G_hibrido.nodes[aid]["nombre"]][1] for aid, _ in puntos_validos]
        centro = [sum(lats) / len(lats), sum(lons) / len(lons)]
    else:
        centro = list(PUNO_CENTRO)

    m = mapa_oscuro(centro, zoom_start=10)

    fg_vuelo = folium.FeatureGroup(name="Ruta aérea (vuelo)", show=True, control=True)
    fg_mar = folium.FeatureGroup(name="Rutas marítimas", show=True)
    fg_tierra = folium.FeatureGroup(name="Rutas terrestres", show=True)

    # ── Ruta aérea desde aeropuerto de origen ──
    if aeropuerto_origen:
        aero_coords = aeropuerto_origen["coords"]
        aero_nombre = aeropuerto_origen["nombre"]
        es_juliaca = False
        if JULIACA_AIRPORT_COORDS is not None:
            es_juliaca = haversine(aero_coords[0], aero_coords[1],
                                   JULIACA_AIRPORT_COORDS[0], JULIACA_AIRPORT_COORDS[1]) < 2.0
            origen_rutas = JULIACA_AIRPORT_COORDS
        else:
            origen_rutas = aero_coords

        folium.Marker(
            location=list(aero_coords),
            tooltip=f"✈ Origen: {aero_nombre}",
            icon=folium.Icon(color="purple", icon="plane", prefix="fa"),
        ).add_to(fg_vuelo)

        if not es_juliaca and JULIACA_AIRPORT_COORDS is not None:
            folium.Marker(
                location=list(JULIACA_AIRPORT_COORDS),
                tooltip=f"✈ Llegada: {JULIACA_AIRPORT_NOMBRE or 'Juliaca'}",
                icon=folium.Icon(color="darkpurple", icon="plane-arrival", prefix="fa"),
            ).add_to(fg_vuelo)
            dist_vuelo = haversine(aero_coords[0], aero_coords[1],
                                   JULIACA_AIRPORT_COORDS[0], JULIACA_AIRPORT_COORDS[1])
            folium.PolyLine(
                locations=[list(aero_coords), list(JULIACA_AIRPORT_COORDS)],
                color="#c084fc", weight=2, dash_array="6,10", opacity=0.85,
                tooltip=f"Vuelo: {aero_nombre} → Juliaca (~{dist_vuelo:.0f} km)",
            ).add_to(fg_vuelo)

        ruta_jul_puno = obtener_ruta_terrestre(origen_rutas, PUERTO_PUNO)
        if ruta_jul_puno:
            folium.PolyLine(
                locations=ruta_jul_puno,
                color="#fb923c", weight=2, opacity=0.50, dash_array="3,5",
                tooltip="Enlace: Juliaca → Puerto de Puno",
            ).add_to(fg_vuelo)
        elif JULIACA_AIRPORT_COORDS is not None:
            dist_aprox = haversine(JULIACA_AIRPORT_COORDS[0], JULIACA_AIRPORT_COORDS[1],
                                   PUERTO_PUNO[0], PUERTO_PUNO[1])
            folium.PolyLine(
                locations=[list(JULIACA_AIRPORT_COORDS), list(PUERTO_PUNO)],
                color="#94a3b8", weight=2, dash_array="4,6", opacity=0.5,
                tooltip=f"Enlace aprox: Juliaca → Puno (~{dist_aprox:.0f} km)",
            ).add_to(fg_vuelo)
    else:
        origen_rutas = PUNO_CENTRO

    folium.Marker(
        location=list(PUERTO_PUNO),
        tooltip="⚓ Puerto de Puno — punto de partida de las rutas marítimas",
        icon=folium.Icon(color="black", icon="anchor", prefix="fa"),
    ).add_to(fg_mar)

    for aid, score in puntos_validos:
        nombre = G_hibrido.nodes[aid]["nombre"]
        categoria = categorias_atractivos.get(nombre, "Otro")
        destino = tuple(coordenadas_atractivos[nombre])
        es_maritimo = requiere_cruce_lacustre(nombre)
        rating = obtener_rating(nombre)
        descripcion = obtener_descripcion(nombre)
        estrellas = styles.generar_estrellas(score)
        _, color = styles.icono_y_color(categoria)

        popup_html = f"""
        <div style="font-family:'Inter',sans-serif;font-size:13px;min-width:200px;background:#2D2F48;color:#B7BDD6;padding:12px;border-radius:10px;">
            <b style="font-size:14px;color:#fff;">{nombre}</b><br>
            <span style="color:#8C93B0;font-size:11px;">{categoria}</span><br><br>
            <b>Motor:</b> {motor_nombre}<br>
            <b>Score:</b> {score:.3f} &nbsp; <span style="color:#FFC857;">{estrellas}</span><br>
            <b>Rating:</b> {rating:.1f} / 5<br>
            <i style="color:#8C93B0;font-size:11px;">{descripcion}</i>
        </div>
        """

        grupo_destino = fg_mar if es_maritimo else fg_tierra
        folium.CircleMarker(
            location=destino, radius=8 + score * 18, color=color,
            fill=True, fill_opacity=0.25, opacity=0.4, weight=1,
        ).add_to(grupo_destino)
        folium.Marker(
            location=destino,
            tooltip=f"{nombre} — score {score:.3f}  {estrellas}",
            popup=folium.Popup(popup_html, max_width=280),
            icon=folium.Icon(
                color="lightblue" if es_maritimo else "lightgray",
                icon="ship" if es_maritimo else "map-pin", prefix="fa",
            ),
        ).add_to(grupo_destino)

        if es_maritimo:
            puerto = puerto_mas_conveniente(destino)
            puerto_coords = puerto["coords"]
            dist_mar_km = haversine(puerto_coords[0], puerto_coords[1], destino[0], destino[1])

            if haversine(PUERTO_PUNO[0], PUERTO_PUNO[1], puerto_coords[0], puerto_coords[1]) > 1.0:
                folium.PolyLine(
                    locations=ruta_terrestre_hacia_puerto(puerto["nombre"], puerto_coords),
                    color="#FFC857", weight=3, opacity=0.75,
                    tooltip=f"Tramo terrestre hasta {puerto['nombre']}",
                ).add_to(fg_mar)
                folium.Marker(
                    location=list(puerto_coords),
                    tooltip=f"Embarque marítimo: {puerto['nombre']}",
                    icon=folium.Icon(color="cadetblue", icon="anchor", prefix="fa"),
                ).add_to(fg_mar)

            folium.PolyLine(
                locations=ruta_curva_maritima(puerto_coords, destino),
                color="#4D96FF", weight=3, dash_array="8,8", opacity=0.9,
                tooltip=f"Ruta marítima a {nombre} (~{dist_mar_km:.1f} km desde {puerto['nombre']})",
            ).add_to(fg_mar)
        else:
            dist_km = haversine(origen_rutas[0], origen_rutas[1], destino[0], destino[1])
            ruta = obtener_ruta_terrestre(origen_rutas, destino)
            if ruta:
                folium.PolyLine(
                    locations=ruta, color="#FFC857", weight=3, opacity=0.85,
                    tooltip=f"Ruta terrestre a {nombre} (~{dist_km:.1f} km aprox.)",
                ).add_to(fg_tierra)
            else:
                folium.PolyLine(
                    locations=[list(origen_rutas), list(destino)],
                    color="#8C93B0", weight=2, dash_array="4,6", opacity=0.7,
                    tooltip=(
                        f"Ruta aprox. a {nombre} (~{dist_km:.1f} km en línea recta — "
                        f"servicio de ruteo no disponible en este momento)"
                    ),
                ).add_to(fg_tierra)

    fg_vuelo.add_to(m)
    fg_mar.add_to(m)
    fg_tierra.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    leyenda_items = []
    if aeropuerto_origen:
        leyenda_items.append('<span style="color:#c084fc;">&#9992;</span> Ruta aérea (vuelo)')
    leyenda_items.append('<span>&#9875;</span> Puerto de partida')
    leyenda_items.append('<span style="color:#4D96FF;">&#9135;</span> Ruta marítima')
    leyenda_items.append('<span style="color:#FFC857;">&#9135;</span> Ruta terrestre')
    leyenda_html = f"""
    <div style="position:fixed;bottom:24px;left:24px;z-index:9999;
                background:rgba(36,38,59,0.95);color:#B7BDD6;
                padding:8px 12px;border-radius:10px;
                box-shadow:0 4px 24px rgba(0,0,0,0.35);
                font-size:11px;font-family:'Inter',sans-serif;
                border:1px solid #3A3D5C;line-height:1.5;">
      <b style="font-size:11px;color:#fff;">Leyenda — {motor_nombre}</b><br>
      {"<br>".join(leyenda_items)}
    </div>
    """
    m.get_root().html.add_child(folium.Element(leyenda_html))
    return m


# ==============================================
# ESTADO
# ==============================================

if "ranking_actual" not in st.session_state:
    st.session_state.ranking_actual = None
if "motor_actual" not in st.session_state:
    st.session_state.motor_actual = None
if "ruta_camino" not in st.session_state:
    st.session_state.ruta_camino = None
if "ruta_distancia" not in st.session_state:
    st.session_state.ruta_distancia = None
if "ruta_origen" not in st.session_state:
    st.session_state.ruta_origen = None
if "ruta_destino" not in st.session_state:
    st.session_state.ruta_destino = None
if "modelos_actualizados" not in st.session_state:
    st.session_state.modelos_actualizados = False
if "aeropuerto_origen" not in st.session_state:
    st.session_state.aeropuerto_origen = None

# ==============================================
# NAVBAR
# ==============================================

st.markdown("""
<div class="navbar">
    <div class="navbar-logo">
        <div class="navbar-logo-icon">🌄</div>
        <div>
            <p class="navbar-title">Recomendador Turístico</p>
            <p class="navbar-subtitle">Región Puno — Perú · Grafo híbrido con ML</p>
        </div>
    </div>
    <div class="navbar-status">
        <span class="navbar-status-dot"></span>
        Sistema activo
    </div>
</div>
""", unsafe_allow_html=True)

DESCRIPCIONES_MOTOR = {
    "Random Walk": (
        "Explora el grafo Usuario–Ítem mediante caminatas aleatorias con reinicio. "
        "Robusto para turistas nuevos sin historial previo."
    ),
    "LightGCN (Deep Learning)": (
        "Propaga y promedia embeddings de usuarios e ítems sobre el grafo de interacciones. "
        "Funciona mejor con usuarios que ya tienen historial."
    ),
    "Meta-recomendador (ML)": (
        "Modelo entrenado que fusiona señales de afinidad del grafo y popularidad "
        "para un ranking combinado."
    ),
}

# ==============================================
# SIDEBAR — SaaS NAV (REDESIGNED)
# ==============================================

nombres = [u["nombre"] for u in usuarios]

# Session state for navigation and persistence
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = "Recomendaciones"
if "usuario_idx" not in st.session_state:
    st.session_state.usuario_idx = 0
if "motor_idx" not in st.session_state:
    st.session_state.motor_idx = 0

# Handle page navigation from query params
if "page" in st.query_params:
    valida = {"Dashboard", "Recomendaciones", "Estadisticas", "Clientes", "Registrar", "Sitios", "Rutas", "Historial", "Config", "Salir"}
    if st.query_params["page"] in valida:
        st.session_state.pagina_actual = st.query_params["page"]

# ── Header ──
st.sidebar.markdown("""
<div class="sb-header">
    <div class="sb-header-icon">SR</div>
    <div class="sb-header-text">
        <p class="sb-header-title">Sistema Inteligente</p>
        <p class="sb-header-sub">de Recomendación Turística</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Helper to render a nav item
def _nav_item(label, page_key):
    is_active = st.session_state.pagina_actual == page_key
    active_class = " active" if is_active else ""
    st.sidebar.markdown(f"""
    <div class="sb-nav-item{active_class}">
        <div class="sb-nav-bar"></div>
        <a class="sb-nav-link" href="?page={page_key}">{label}</a>
    </div>
    """, unsafe_allow_html=True)

# ── Navigation ──
st.sidebar.markdown(
    '<div class="sb-section-label">PRINCIPAL</div>', unsafe_allow_html=True
)
_nav_item("Dashboard", "Dashboard")
_nav_item("Recomendaciones", "Recomendaciones")
_nav_item("Estadísticas", "Estadisticas")

st.sidebar.markdown(
    '<div class="sb-section-label">GESTIÓN</div>', unsafe_allow_html=True
)
_nav_item("Clientes", "Clientes")
_nav_item("Registrar Cliente", "Registrar")
_nav_item("Sitios Turísticos", "Sitios")
_nav_item("Rutas Turísticas", "Rutas")

st.sidebar.markdown(
    '<div class="sb-section-label">SISTEMA</div>', unsafe_allow_html=True
)
_nav_item("Historial", "Historial")
_nav_item("Configuración", "Config")
_nav_item("Cerrar sesión", "Salir")

st.sidebar.markdown(
    '<div class="sb-divider"></div>', unsafe_allow_html=True
)

# ── Controls area per page ──
pagina = st.session_state.pagina_actual

st.sidebar.markdown(f'<div class="sb-controls">', unsafe_allow_html=True)

# Variables with default values (overridden below)
idx_u = st.session_state.usuario_idx
usuario_nombre = nombres[idx_u]
usuario_id = next(u["id"] for u in usuarios if u["nombre"] == usuario_nombre)
prefs = next(u["preferencias"] for u in usuarios if u["nombre"] == usuario_nombre)
idx_m = st.session_state.motor_idx
motor = list(DESCRIPCIONES_MOTOR.keys())[idx_m]
generar = False

if pagina == "Recomendaciones":
    idx_u = st.session_state.usuario_idx
    n_usuario = st.selectbox("Turista", nombres, index=idx_u, key="sb_turista")
    st.session_state.usuario_idx = nombres.index(n_usuario)
    usuario_nombre = n_usuario
    usuario_id = next(u["id"] for u in usuarios if u["nombre"] == usuario_nombre)
    prefs = next(u["preferencias"] for u in usuarios if u["nombre"] == usuario_nombre)
    if prefs:
        st.markdown(
            f'<div style="font-size:0.7rem;color:#8C93B0;margin:-4px 0 12px;">'
            f'Preferencias: <span style="color:#B7BDD6;">{", ".join(prefs)}</span></div>',
            unsafe_allow_html=True,
        )
    idx_m = st.session_state.motor_idx
    lista_motores = list(DESCRIPCIONES_MOTOR.keys())
    n_motor = st.selectbox("Motor de recomendación", lista_motores, index=idx_m, key="sb_motor")
    st.session_state.motor_idx = lista_motores.index(n_motor)
    motor = n_motor
    st.info(DESCRIPCIONES_MOTOR[motor])

    with st.expander("Aeropuerto de origen", expanded=False):
        st.caption("Elige el aeropuerto desde donde parte el turista. Se dibujará la ruta aérea hasta Juliaca.")
        opciones = ["— Ninguno (iniciar desde Puno) —"] + sorted(AEROPUERTOS_PERU.keys())
        sel = st.selectbox("Origen del vuelo", opciones, key="sb_aeropuerto")
        if sel == opciones[0]:
            st.session_state.aeropuerto_origen = None
        else:
            info = AEROPUERTOS_PERU[sel]
            st.session_state.aeropuerto_origen = {"nombre": sel, **info}

    generar = st.button("Generar recomendaciones", key="sb_generar")

elif pagina == "Clientes" or pagina == "Registrar":
    idx_u = st.session_state.usuario_idx
    n_usuario = st.selectbox("Turista", nombres, index=idx_u, key="sb_turista_c")
    st.session_state.usuario_idx = nombres.index(n_usuario)
    usuario_nombre = n_usuario
    usuario_id = next(u["id"] for u in usuarios if u["nombre"] == usuario_nombre)
    prefs = next(u["preferencias"] for u in usuarios if u["nombre"] == usuario_nombre)
    if prefs:
        st.markdown(
            f'<div style="font-size:0.7rem;color:#8C93B0;margin:-4px 0 12px;">'
            f'Preferencias: <span style="color:#B7BDD6;">{", ".join(prefs)}</span></div>',
            unsafe_allow_html=True,
        )
    st.markdown("""
        <div style="font-size:0.72rem;font-weight:600;color:#5A5F7A;text-transform:uppercase;letter-spacing:0.05em;margin:8px 0 4px;">Registrar nuevo turista</div>
    """, unsafe_allow_html=True)
    with st.form("registro_usuario"):
        nuevo_nombre = st.text_input("Nombre completo")
        nueva_edad = st.number_input("Edad", min_value=0, max_value=120, value=30, step=1)
        nuevas_prefs = st.multiselect(
            "Preferencias",
            ["lago", "isla", "arqueologico", "religioso", "mirador", "museo", "evento", "senderismo"],
        )
        submitted = st.form_submit_button("Registrar", use_container_width=True)
        if submitted and nuevo_nombre and nuevas_prefs:
            guardar_nuevo_usuario(nuevo_nombre, nuevas_prefs, edad=int(nueva_edad))
            st.session_state["mensaje_registro"] = (
                f"✅ Turista '{nuevo_nombre}' registrado exitosamente"
            )
            st.rerun()
    if st.session_state.get("mensaje_registro"):
        st.success(st.session_state.pop("mensaje_registro"))

elif pagina == "Sitios":
    st.markdown(
        '<div style="font-size:0.82rem;color:#B7BDD6;">Explora los atractivos turísticos disponibles en el mapa principal.</div>',
        unsafe_allow_html=True,
    )

elif pagina == "Rutas":
    st.markdown(
        '<div style="font-size:0.82rem;color:#B7BDD6;">Usa el planificador de rutas en la sección inferior de la página principal.</div>',
        unsafe_allow_html=True,
    )

elif pagina == "Dashboard":
    st.markdown(
        '<div style="font-size:0.82rem;color:#B7BDD6;">Bienvenido al sistema. Selecciona <strong>Recomendaciones</strong> para comenzar.</div>',
        unsafe_allow_html=True,
    )

elif pagina == "Historial" or pagina == "Config":
    st.markdown(
        '<div style="font-size:0.82rem;color:#8C93B0;">Sección en desarrollo.</div>',
        unsafe_allow_html=True,
    )

elif pagina == "Estadisticas":
    st.markdown(
        '<div style="font-size:0.82rem;color:#8C93B0;">Próximamente — Estadísticas de visitas y recomendaciones.</div>',
        unsafe_allow_html=True,
    )

elif pagina == "Salir":
    st.markdown(
        '<div style="font-size:0.82rem;color:#FF5E78;">Sesión finalizada. Recarga la página para continuar.</div>',
        unsafe_allow_html=True,
    )

st.sidebar.markdown(f'</div>', unsafe_allow_html=True)

# ── Bottom user panel ──
st.sidebar.markdown("""
<div class="sb-user-panel">
    <div class="sb-user-avatar">A</div>
    <div class="sb-user-info">
        <p class="sb-user-name">Administrador</p>
        <p class="sb-user-role">Sistema de Recomendación Turística</p>
    </div>
</div>
""", unsafe_allow_html=True)

if generar:
    if not st.session_state.modelos_actualizados and motor != "Random Walk":
        with st.spinner("Actualizando modelos con nuevos datos..."):
            from reentrenar import reentrenar_modelos
            reentrenar_modelos()
        st.session_state.modelos_actualizados = True
    with st.spinner("Procesando..."):
        if motor == "Random Walk":
            ranking = recomendar(usuario_id)
        elif motor == "LightGCN (Deep Learning)":
            ranking = recomendar_lightgcn(usuario_id)
        else:
            ranking = recomendar_meta(usuario_id)

        edad_usuario = next((u.get("edad") for u in usuarios if u["id"] == usuario_id), None)
        if edad_usuario is not None:
            ranking = reordenar_por_edad(ranking, edad_usuario)

    st.session_state.ranking_actual = ranking
    st.session_state.motor_actual = motor

ranking_activo = st.session_state.ranking_actual
motor_activo = st.session_state.motor_actual

# ==============================================
# MAIN CONTENT
# ==============================================

if ranking_activo and motor_activo:
    col_izq, col_der = st.columns([0.9, 1.6])

    with col_izq:
        st.markdown(
            f'<div class="section-label">Resultados · '
            f'<span style="color:var(--primary);font-weight:400;">{motor_activo}</span></div>',
            unsafe_allow_html=True,
        )
        if not ranking_activo:
            st.warning("No se encontraron recomendaciones. Prueba con otro turista.")
        else:
            for aid, score in ranking_activo:
                if aid not in G_hibrido.nodes:
                    continue
                nombre = G_hibrido.nodes[aid]["nombre"]
                categoria = categorias_atractivos.get(nombre, "Otro")
                zona = G_hibrido.nodes[aid].get("zona") or "No especificada"
                rating = obtener_rating(nombre)
                descripcion = obtener_descripcion(nombre)
                es_maritimo = requiere_cruce_lacustre(nombre)

                st.markdown(
                    styles.tarjeta_lugar_html(
                        nombre=nombre,
                        categoria=categoria,
                        zona=zona,
                        score=score,
                        rating=rating,
                        es_maritimo=es_maritimo,
                        descripcion=descripcion,
                    ),
                    unsafe_allow_html=True,
                )
                if st.button("Visité este lugar", key=f"visit_{aid}"):
                    registrar_visita(usuario_id, aid, peso=1.0)
                    st.session_state.modelos_actualizados = False
                    st.success(f"Visita a {nombre} registrada")

    with col_der:
        st.markdown(
            f'<div class="section-label">Mapa de rutas · '
            f'<span style="color:var(--primary);font-weight:400;">{motor_activo}</span></div>',
            unsafe_allow_html=True,
        )
        with st.spinner("Calculando rutas..."):
            mapa = crear_mapa_resultados(ranking_activo, motor_activo,
                                         aeropuerto_origen=st.session_state.get("aeropuerto_origen"))
        st_folium(mapa, width=None, height=580, returned_objects=[])

else:
    st.markdown('<div class="section-label">Mapa de atractivos · capas por categoría</div>', unsafe_allow_html=True)
    mapa_vacio = mapa_oscuro(list(PUNO_CENTRO), zoom_start=10)
    overlay_html = """
    <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                z-index: 9999; background: rgba(8,13,26,0.88); color:#c8d0e8;
                padding: 20px 28px; border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.7);
                font-size: 14px; font-family: 'Inter', sans-serif;
                border: 1px solid rgba(255,255,255,0.12); text-align:center;">
      <span style="font-size:28px;">🗺️</span><br><br>
      <b style="font-size:15px; color:#eef1fb;">Elige un motor y genera recomendaciones</b><br>
      <span style="color:#888; font-size:12px;">Los lugares y rutas aparecerán aquí</span>
    </div>
    """
    mapa_vacio.get_root().html.add_child(folium.Element(overlay_html))
    agregar_capas_por_categoria(mapa_vacio, coordenadas_atractivos, categorias_atractivos)
    st_folium(mapa_vacio, width=None, height=560, returned_objects=[])

# ==============================================
# PLANIFICADOR DE RUTAS
# ==============================================

with st.expander("Planificador de rutas (A*)", expanded=False):
    opciones_validas = [n for n in coordenadas_atractivos if n in G_rutas.nodes]

    if len(opciones_validas) < 2:
        st.warning("No hay suficientes atractivos con coordenadas para planificar rutas.")
    else:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            origen = st.selectbox("Origen", opciones_validas, key="origen_ruta")
        with col_r2:
            destino = st.selectbox("Destino", opciones_validas, key="destino_ruta")

        col_b1, col_b2, _ = st.columns([1, 1, 2])
        with col_b1:
            calcular = st.button("Calcular ruta", use_container_width=True, type="primary")
        with col_b2:
            limpiar = st.button("Limpiar ruta", use_container_width=True)

        if limpiar:
            st.session_state.ruta_camino = None
            st.rerun()

        if calcular:
            if origen == destino:
                st.warning("El origen y destino deben ser diferentes")
                st.session_state.ruta_camino = None
            else:
                try:
                    def heuristic(u, v):
                        lat_u, lon_u = G_rutas.nodes[u]['lat'], G_rutas.nodes[u]['lon']
                        lat_v, lon_v = G_rutas.nodes[v]['lat'], G_rutas.nodes[v]['lon']
                        return haversine(lat_u, lon_u, lat_v, lon_v)

                    camino = nx.astar_path(G_rutas, origen, destino, heuristic=heuristic, weight='weight')
                    distancia_total = sum(
                        G_rutas[camino[i]][camino[i + 1]]['distancia_km'] for i in range(len(camino) - 1)
                    )
                    tramos_maritimos = sum(
                        1 for i in range(len(camino) - 1)
                        if G_rutas[camino[i]][camino[i + 1]].get('maritimo', False)
                    )

                    st.session_state.ruta_camino = camino
                    st.session_state.ruta_distancia = distancia_total
                    st.session_state.ruta_origen = origen
                    st.session_state.ruta_destino = destino
                    st.session_state.ruta_tramos_maritimos = tramos_maritimos
                except nx.NetworkXNoPath:
                    st.error("No existe ruta entre los puntos seleccionados")
                    st.session_state.ruta_camino = None
                except Exception as e:
                    st.error(f"Error al calcular la ruta: {e}")
                    st.session_state.ruta_camino = None

        if st.session_state.get('ruta_camino') is not None:
            camino = st.session_state.ruta_camino
            distancia_total = st.session_state.ruta_distancia
            origen = st.session_state.ruta_origen
            destino = st.session_state.ruta_destino
            tramos_maritimos = st.session_state.get('ruta_tramos_maritimos', 0)

            texto_maritimo = (
                f" · {tramos_maritimos} tramo(s) requieren cruce en lancha"
                if tramos_maritimos else " · ruta íntegramente por tierra"
            )
            st.success(f"Ruta óptima — Distancia total: {distancia_total:.2f} km{texto_maritimo}")
            st.markdown(f"**Recorrido:** {' → '.join(camino)}")

            latitudes = [coordenadas_atractivos[nombre][0] for nombre in camino]
            longitudes = [coordenadas_atractivos[nombre][1] for nombre in camino]
            centro_lat = sum(latitudes) / len(latitudes)
            centro_lon = sum(longitudes) / len(longitudes)

            mapa_ruta = mapa_oscuro([centro_lat, centro_lon], zoom_start=11)

            capa_ruta = folium.FeatureGroup(name="Ruta calculada", show=True)
            folium.Marker(
                coordenadas_atractivos[origen], popup=f"Origen: {origen}",
                icon=folium.Icon(color='green', icon='play', prefix='fa'),
            ).add_to(capa_ruta)
            folium.Marker(
                coordenadas_atractivos[destino], popup=f"Destino: {destino}",
                icon=folium.Icon(color='red', icon='flag', prefix='fa'),
            ).add_to(capa_ruta)
            for nombre in camino[1:-1]:
                folium.Marker(
                    coordenadas_atractivos[nombre], popup=nombre,
                    icon=folium.Icon(color='lightblue', icon='info-sign', prefix='fa'),
                ).add_to(capa_ruta)

            capa_tierra = folium.FeatureGroup(name="Tramos por tierra", show=True)
            capa_lancha = folium.FeatureGroup(name="Tramos en lancha (cruce del lago)", show=True)
            for i in range(len(camino) - 1):
                punto_a = tuple(coordenadas_atractivos[camino[i]])
                punto_b = tuple(coordenadas_atractivos[camino[i + 1]])
                es_maritimo = G_rutas[camino[i]][camino[i + 1]].get('maritimo', False)
                if es_maritimo:
                    folium.PolyLine(
                        ruta_curva_maritima(punto_a, punto_b),
                        color='#4D96FF', weight=5, opacity=0.85, dash_array='8, 8',
                        tooltip=f"En lancha: {camino[i]} → {camino[i+1]}",
                    ).add_to(capa_lancha)
                else:
                    ruta_real = obtener_ruta_terrestre(punto_a, punto_b)
                    folium.PolyLine(
                        ruta_real if ruta_real else [list(punto_a), list(punto_b)],
                        color='#6C63FF', weight=5, opacity=0.85,
                        tooltip=f"Por tierra: {camino[i]} → {camino[i+1]}",
                    ).add_to(capa_tierra)

            capa_ruta.add_to(mapa_ruta)
            capa_tierra.add_to(mapa_ruta)
            capa_lancha.add_to(mapa_ruta)
            folium.LayerControl(collapsed=False).add_to(mapa_ruta)

            st_folium(mapa_ruta, width=None, height=450, key="mapa_ruta")

# ==============================================
# FOOTER
# ==============================================

st.markdown(
    '<div class="footer">'
    'Sistema de Recomendación Turística Inteligente — Región Puno, Perú &ensp;·&ensp; '
    'Hecho con Streamlit &ensp;·&ensp; Datos OSM y CSV 2019–2024'
    '</div>',
    unsafe_allow_html=True,
)
