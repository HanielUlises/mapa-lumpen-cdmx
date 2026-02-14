import folium
import pandas as pd
import requests
import json
from folium.features import GeoJsonTooltip

df = pd.read_csv('marginacion_cdmx.csv', encoding='utf-8')

df['nombre_col'] = df['nombre de la colonia'].astype(str).str.strip().str.upper() \
    .str.replace(r'^COL\.?\s*', '', regex=True) \
    .str.replace(r'^COLONIA\s*', '', regex=True) \
    .str.replace(r'^AMPL?\.?\s*', '', regex=True) \
    .str.replace(r'^AMPLIACION\s*', '', regex=True) \
    .str.replace(r'\s+', ' ', regex=True) \
    .str.replace(r'Á', 'A', regex=True).str.replace(r'É', 'E', regex=True) \
    .str.replace(r'Í', 'I', regex=True).str.replace(r'Ó', 'O', regex=True) \
    .str.replace(r'Ú', 'U', regex=True).str.replace(r'Ñ', 'N', regex=True)

df['grado'] = df['grado de marginación'].astype(str).str.strip().str.title()

geojson_path = 'catalogo-colonias.geojson'
try:
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
except FileNotFoundError:
    geojson_url = "https://raw.githubusercontent.com/open-mexico/mexico-geojson/main/09-Cdmx.geojson"
    response = requests.get(geojson_url)
    response.raise_for_status()
    geojson_data = response.json()

USE_CP_JOIN = 'd_codigo' in geojson_data['features'][0]['properties'] if 'features' in geojson_data else False
NOMBRE_FIELD = 'nom_col'

m = folium.Map(location=[19.4326, -99.1332], zoom_start=11, tiles='CartoDB positron')

def get_color(grado):
    grado = str(grado).title()
    if 'Muy Alto' in grado:
        return '#8B0000'
    elif 'Alto' in grado:
        return '#FF4500'
    elif 'Medio' in grado:
        return '#FFA500'
    elif 'Bajo' in grado:
        return '#FFD700'
    elif 'Muy Bajo' in grado:
        return '#90EE90'
    return '#D3D3D3'

def style_function(feature):
    if USE_CP_JOIN:
        key = feature['properties'].get('d_codigo', '').strip()
        match = df[df['código postal'].astype(str).str.strip() == key]
    else:
        nombre_geo = str(feature['properties'].get(NOMBRE_FIELD, '')).strip().upper()
        nombre_geo = nombre_geo.replace(r'^COL\.?\s*', '').replace(r'^COLONIA\s*', '') \
                               .replace(r'^AMPL?\.?\s*', '').replace(r'^AMPLIACION\s*', '') \
                               .replace(r'\s+', ' ').replace('Á', 'A').replace('É', 'E') \
                               .replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U').replace('Ñ', 'N')
        match = df[df['nombre_col'] == nombre_geo]

    if not match.empty:
        grado = match['grado'].iloc[0]
        opacity = 0.7
    else:
        grado = 'Sin dato'
        opacity = 0.3

    return {
        'fillColor': get_color(grado),
        'color': '#555555',
        'weight': 0.6,
        'fillOpacity': opacity
    }

folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=GeoJsonTooltip(
        fields=[NOMBRE_FIELD if not USE_CP_JOIN else 'd_codigo'],
        aliases=['Colonia:' if not USE_CP_JOIN else 'C.P.:'],
        sticky=True
    )
).add_to(m)

legend_html = '''
<div style="position: fixed; bottom: 50px; left: 50px; width: 240px; height: 200px; 
border:2px solid grey; z-index:9999; font-size:14px; background:white; padding:10px; opacity:0.9;">
<b>Grado Marginación 2020</b><br>
<i style="background:#8B0000">&nbsp;&nbsp;</i> Muy Alto<br>
<i style="background:#FF4500">&nbsp;&nbsp;</i> Alto<br>
<i style="background:#FFA500">&nbsp;&nbsp;</i> Medio<br>
<i style="background:#FFD700">&nbsp;&nbsp;</i> Bajo<br>
<i style="background:#90EE90">&nbsp;&nbsp;</i> Muy Bajo<br>
<i style="background:#D3D3D3">&nbsp;&nbsp;</i> Sin dato
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

m.save('index.html')