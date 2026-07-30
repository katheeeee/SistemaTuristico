import pandas as pd
import numpy as np
import random
import os

# Configuraciones
years = [2019, 2020, 2021, 2022, 2023, 2024]
meses_dict = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}
# Cargar sitios desde OSM
osm_path = r'C:\Users\franc\Desktop\puno_recommender\data\lugares_puno_osm.csv'
if os.path.exists(osm_path):
    df_osm = pd.read_csv(osm_path)
    # Seleccionar 80 lugares al azar para mantener el dataset en un tamaño manejable (o todos si son menos)
    n_sitios = min(80, len(df_osm))
    sitios = df_osm.sample(n=n_sitios, random_state=42)['nombre'].tolist()
else:
    sitios = [
        "Lago Titicaca", "Islas de los Uros", "Isla Taquile", "Isla Amantaní", 
        "Sillustani", "Chucuito (Inca Uyo)", "Lampa", "Complejo Arqueológico de Pucará", 
        "Juli", "Aramu Muru (Puerta de Hayu Marca)", "Cañón de Tinajani", 
        "Catedral de Puno", "Mirador del Puma Uta", "Mirador Kuntur Wasi", "Cerrito de Huajsapata"
    ]
nacionalidades = ['Peruano', 'Estadounidense', 'Europeo', 'Latinoamericano', 'Asiatico']
transportes = ['Transporte público', 'Tour organizado', 'Transporte privado', 'Taxi']

# Clima aproximado de Puno por mes
clima = {
    1: {'temp': 9.0, 'precip': 120},
    2: {'temp': 8.8, 'precip': 110},
    3: {'temp': 8.5, 'precip': 90},
    4: {'temp': 8.0, 'precip': 40},
    5: {'temp': 7.0, 'precip': 15},
    6: {'temp': 5.5, 'precip': 5},
    7: {'temp': 5.0, 'precip': 5},
    8: {'temp': 6.0, 'precip': 10},
    9: {'temp': 7.5, 'precip': 25},
    10: {'temp': 8.5, 'precip': 40},
    11: {'temp': 9.0, 'precip': 60},
    12: {'temp': 9.2, 'precip': 90}
}

data = []
row_id = 1

for y in years:
    for m, mes_nombre in meses_dict.items():
        # Definir temporada y festividad
        temporada = 'Alta' if m in [5, 6, 7, 8, 9, 10] else 'Baja'
        festividad = 'Ninguna'
        tiene_festividad = 0
        if m == 2:
            festividad = 'Fiesta de la Candelaria'
            tiene_festividad = 1
        elif m == 6:
            festividad = 'Año Nuevo Andino'
            tiene_festividad = 1
        elif m == 11:
            festividad = 'Aniversario de Puno'
            tiene_festividad = 1

        # Efecto pandemia
        if y == 2020 and m >= 3:
            visitante_mult = 0.1
        elif y == 2021:
            visitante_mult = 0.4
        elif y == 2023 and m <= 3:
            visitante_mult = 0.3 # Protestas
        else:
            visitante_mult = 1.0
            
        if temporada == 'Alta':
            visitante_mult *= 1.5
        if tiene_festividad:
            visitante_mult *= 2.0

        for sitio in sitios:
            for nac in nacionalidades:
                # Generar numero de visitantes aleatorio
                base_vis = random.randint(50, 400) if nac == 'Peruano' else random.randint(10, 200)
                num_visitantes = int(base_vis * visitante_mult * random.uniform(0.8, 1.2))
                
                temp_c = round(random.gauss(clima[m]['temp'], 1.0), 1)
                precip = round(random.gauss(clima[m]['precip'], 10.0), 1)
                precip = max(0, precip)
                
                satisfaccion = round(random.uniform(3.5, 5.0), 1)
                gasto = round(random.uniform(30.0, 80.0) if nac == 'Peruano' else random.uniform(70.0, 150.0), 2)
                transporte = random.choice(transportes)
                
                # Para islas y lago, el transporte publico es menos comun
                if 'Isla' in sitio or 'Lago' in sitio:
                    if transporte == 'Transporte público' or transporte == 'Taxi':
                        transporte = 'Tour organizado'

                data.append([
                    row_id, y, m, mes_nombre, sitio, temporada, festividad, tiene_festividad,
                    nac, num_visitantes, temp_c, precip, satisfaccion, gasto, transporte
                ])
                row_id += 1

columns = [
    'id', 'anio', 'mes_num', 'mes', 'sitio_turistico', 'temporada', 
    'festividad', 'tiene_festividad', 'nacionalidad', 'num_visitantes', 
    'temperatura_promedio_c', 'precipitacion_mm', 'satisfaccion_1_5', 
    'gasto_promedio_soles', 'tipo_transporte'
]

df = pd.DataFrame(data, columns=columns)

# Guardar en CSV
output_path = r'C:\Users\franc\Desktop\puno_recommender\data\turismo_puno_2019_2024.csv'
df.to_csv(output_path, index=False, encoding='utf-8')
print(f'Dataset generado con {len(df)} filas exitosamente en: {output_path}')
