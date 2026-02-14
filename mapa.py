import folium
import pandas as pd
from folium.features import GeoJsonTooltip
import json
import requests

df = pd.read_csv('marginacion_cdmx.csv', encoding='utf-8')

df = df[df['clave de la entidad'] == '09'].copy()

df['nombre_col'] = df['nombre de la colonia'].astype(str).str.strip().str.upper() \
    .str.replace(r'^COL\.?\s*', '', regex=True) \
    .str.replace(r'^COLONIA\s*', '', regex=True) \
    .str.replace(r'\s+', ' ', regex=True)

df['grado'] = df['grado de marginación'].astype(str).str.strip().str.title()

print("Colonias en tus datos (muestra):", df['nombre_col'].head(10).tolist())
print("Grados disponibles:", df['grado'].value_counts().to_dict())

# 2. GeoJSON con nombres reales (usa este de CDMX datos abiertos - descarga una vez o usa URL si disponible)
# Si descargaste: https://datos.cdmx.gob.mx/dataset/catalogo-de-colonias-datos-abiertos/resource/026b42d3-a609-44c7-a83d-22b2150caffc/download/catalogo-colonias.geojson
# Guárdalo como 'colonias_cdmx.geojson' y usa:
# with open('colonias_cdmx.geojson', 'r', encoding='utf-8') as f:
#     geojson_data = json.load(f)

# Alternativa temporal: usa un GeoJSON público con nombres (ej. de PhantomInsights o similar, pero mejor descarga el oficial)
geojson_url = "https://raw.githubusercontent.com/angel-cervantes/cdmx-geojson/main/colonias.geojson"  # ejemplo alternativo con NOMBRE
# Si no carga, descarga de https://datos.cdmx.gob.mx y usa local
response = requests.get(geojson_url)
if response.status_code == 200:
    geojson_data = response.json()
else:
    print("Error cargando GeoJSON remoto, descarga manual de https://datos.cdmx.gob.mx y usa local")
    # Descomenta y ajusta:
    # with open('colonias_cdmx.geojson', 'r', encoding='utf-8') as f:
    #     geojson_data = json.load(f)

# Campo de nombre en GeoJSON (cambia según el archivo: suele ser 'nom_col', 'NOMBRE', 'nombre')
NOMBRE_FIELD = 'nom_col'  # o 'NOMBRE' o 'nombre_colonia' - revisa con print(geojson_data['features'][0]['properties'])

# 3. Mapa
m = folium.Map(location=[19.4326, -99.1332], zoom_start=11, tiles='CartoDB positron')

def get_color(grado):
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
    else:
        return '#D3D3D3'

def style_function(feature):
    nombre_geo = feature['properties'].get(NOMBRE_FIELD, '').strip().upper()
    nombre_geo = nombre_geo.replace('COL. ', '').replace('COLONIA ', '').strip()
    
    match = df[df['nombre_col'] == nombre_geo]
    if not match.empty:
        grado = match['grado'].iloc[0]
        fill_op = 0.7
    else:
        grado = 'Sin dato'
        fill_op = 0.3
    
    return {
        'fillColor': get_color(grado),
        'color': '#555555',
        'weight': 0.5,
        'fillOpacity': fill_op
    }

folium.GeoJson(
    geojson_data,
    name='Colonias CDMX',
    style_function=style_function,
    tooltip=GeoJsonTooltip(
        fields=[NOMBRE_FIELD],
        aliases=['Colonia:'],
        localize=True,
        sticky=True
    )
).add_to(m)

legend_html = '''
<div style="position: fixed; bottom: 50px; left: 50px; width: 240px; height: 200px; 
border:2px solid grey; z-index:9999; font-size:14px; background-color:white; 
padding: 10px; border-radius:5px; opacity:0.9;">
<b>Grado de Marginación Urbana 2020</b><br>
<i style="background:#8B0000">&nbsp;&nbsp;&nbsp;</i> Muy Alto<br>
<i style="background:#FF4500">&nbsp;&nbsp;&nbsp;</i> Alto<br>
<i style="background:#FFA500">&nbsp;&nbsp;&nbsp;</i> Medio<br>
<i style="background:#FFD700">&nbsp;&nbsp;&nbsp;</i> Bajo<br>
<i style="background:#90EE90">&nbsp;&nbsp;&nbsp;</i> Muy Bajo<br>
<i style="background:#D3D3D3">&nbsp;&nbsp;&nbsp;</i> Sin dato
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

m.save('index.html')