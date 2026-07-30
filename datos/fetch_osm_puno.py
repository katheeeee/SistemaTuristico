import requests
import pandas as pd
import json

def fetch_osm_data():
    print("Obteniendo datos de OpenStreetMap para Puno...")
    # Bounding box aproximado de la región del Lago Titicaca y Puno
    # sur, oeste, norte, este
    bbox = "-16.5,-71.0,-14.5,-69.0"
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:50];
    (
      node["tourism"]({bbox});
      node["historic"]({bbox});
      node["amenity"="viewpoint"]({bbox});
    );
    out body;
    """
    headers = {'User-Agent': 'PunoRecommenderApp/1.0'}
    response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers)
    if response.status_code != 200:
        print(f"Error from Overpass: {response.status_code}")
        print(response.text)
        return
    data = response.json()
    
    places = []
    seen_names = set()
    
    # Agregar algunos sitios manuales muy famosos por si no están mapeados como nodos en OSM
    manual_sites = [
        {"nombre": "Lago Titicaca", "categoria": "Naturaleza", "latitud": -15.836, "longitud": -69.335},
        {"nombre": "Islas de los Uros", "categoria": "Isla", "latitud": -15.820, "longitud": -69.963},
        {"nombre": "Isla Taquile", "categoria": "Isla", "latitud": -15.766, "longitud": -69.683},
        {"nombre": "Isla Amantaní", "categoria": "Isla", "latitud": -15.666, "longitud": -69.716},
        {"nombre": "Cañón de Tinajani", "categoria": "Naturaleza", "latitud": -14.935, "longitud": -70.627},
    ]
    
    for s in manual_sites:
        places.append(s)
        seen_names.add(s["nombre"].lower())
        
    for element in data['elements']:
        if 'tags' in element and 'name' in element['tags']:
            name = element['tags']['name']
            if name.lower() in seen_names:
                continue
                
            lat = element.get('lat')
            lon = element.get('lon')
            if not lat or not lon:
                continue
                
            tags = element['tags']
            categoria = "Sitio Arqueológico"
            
            if tags.get('tourism') in ['hotel', 'hostel', 'guest_house', 'motel']:
                categoria = "Hotel"
            elif tags.get('tourism') in ['museum', 'gallery']:
                categoria = "Museo"
            elif tags.get('tourism') == 'viewpoint' or tags.get('amenity') == 'viewpoint':
                categoria = "Mirador"
            elif tags.get('historic') in ['ruins', 'archaeological_site']:
                categoria = "Sitio Arqueológico"
            elif tags.get('historic') == 'church' or tags.get('building') == 'church':
                categoria = "Patrimonio Religioso"
            elif tags.get('tourism') == 'restaurant':
                categoria = "Restaurante"
            else:
                categoria = "Mirador" # Fallback genérico para otros tourism
                
            places.append({
                "nombre": name,
                "categoria": categoria,
                "latitud": lat,
                "longitud": lon
            })
            seen_names.add(name.lower())
            
    df = pd.DataFrame(places)
    # Filtrar lugares sin nombre o muy cortos
    df = df[df['nombre'].str.len() > 3]
    # Eliminar duplicados
    df = df.drop_duplicates(subset=['nombre'])
    
    output_path = r'C:\Users\franc\Desktop\puno_recommender\data\lugares_puno_osm.csv'
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"Descargados {len(df)} lugares exitosamente en {output_path}")

if __name__ == "__main__":
    fetch_osm_data()
