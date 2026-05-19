# demo.py
import streamlit as st
import sys
import os
import folium
from streamlit_folium import st_folium

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.grafo_hibrido import G_hibrido
from src.recomendador import recomendar
from src.datos_puno import usuarios, coordenadas_atractivos
from src.meta_recomendador import recomendar_meta
from src.lightgcn_model import recomendar_lightgcn  # Importar LightGCN

st.set_page_config(page_title="Recomendador Turístico Puno", layout="wide")
st.title("Sistema de Recomendación Turística Inteligente")
st.markdown("Basado en un grafo híbrido (colaborativo + contenido)")

col_izq, col_der = st.columns([1.2, 1.8], gap="medium")

with col_izq:
    st.subheader("Turista")
    nombres = [u["nombre"] for u in usuarios]
    usuario_nombre = st.selectbox("Selecciona un turista", nombres, label_visibility="collapsed")
    usuario_id = next(u["id"] for u in usuarios if u["nombre"] == usuario_nombre)
    
    prefs = next(u["preferencias"] for u in usuarios if u["nombre"] == usuario_nombre)
    st.write(f"Preferencias: {', '.join(prefs)}")
    
    # Selector con tres motores
    motor = st.selectbox(
        "Motor de recomendación",
        ["Random Walk (actual)", "LightGCN (deep learning)", "Meta-recomendador (ML)"]
    )
    
    if st.button("Recomendar atractivos", type="primary", use_container_width=True):
        with st.spinner("Procesando recomendaciones..."):
            if motor == "Random Walk (actual)":
                recomendaciones = recomendar(usuario_id)
            elif motor == "LightGCN (deep learning)":
                recomendaciones = recomendar_lightgcn(usuario_id)
            else:
                recomendaciones = recomendar_meta(usuario_id)
        
        if recomendaciones:
            st.subheader("Top lugares recomendados")
            for i, (aid, score) in enumerate(recomendaciones):
                nombre = G_hibrido.nodes[aid]["nombre"]
                tipo = G_hibrido.nodes[aid].get("tipo_atractivo", "")
                zona = G_hibrido.nodes[aid].get("zona", "")
                st.markdown(f"""
**{i+1}. {nombre}**  
Tipo: {tipo} | Zona: {zona}  
Puntuacion: {score:.3f}
""")
                st.divider()
        else:
            st.warning("No se encontraron recomendaciones. Prueba con otro usuario.")

with col_der:
    st.subheader("Mapa de Atractivos Turisticos - Puno")
    
    mapa = folium.Map(location=[-15.840, -69.900], zoom_start=10)
    
    for nombre, (lat, lon) in coordenadas_atractivos.items():
        folium.Marker(
            [lat, lon],
            popup=nombre,
            icon=folium.Icon(color="green", icon="info-sign", prefix='fa')
        ).add_to(mapa)
    
    st_folium(mapa, width=700, height=550, returned_objects=[])
    st.caption("Haz clic en los marcadores para ver el nombre del atractivo.")