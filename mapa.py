import folium
import pandas as pd
import requests
from folium.features import GeoJsonTooltip

df = pd.read_csv('marginacion_cdmx.csv', encoding='utf-8')

df['nombre_col'] = df['nombre de la colonia'].astype(str).str.strip().str.upper() \
    .str.replace(r'^COL\.?\s*', '', regex=True) \
    .str.replace(r'^COLONIA\s*', '', regex=True) \
    .str.replace(r'^AMPL\s*', '', regex=True) \
    .str.replace(r'^AMPLIACION\s*', '', regex=True) \
    .str.replace(r'^AMP\s*', '', regex=True) \
    .str.replace(r'\s+', ' ', regex=True) \
    .str.replace('Á', 'A').str.replace('É', 'E').str.replace('Í', 'I').str.replace('Ó', 'O').str.replace('Ú', 'U') \
    .str.replace('Ñ', 'N') 

df['grado'] = df['grado de marginación'].astype(str).str.strip().str.title()

print("Colonias cargadas en CSV:", len(df))
print("Muestra nombres limpios:", df['nombre_col'].head(8).tolist())
print("Grados únicos:", df['grado'].value_counts().to_dict())

geojson_url = "https://raw.githubusercontent.com/angel-cervantes/cdmx-geojson/main/colonias.geojson"
response = requests.get(geojson_url)
if response.status_code != 200:
    print("Error cargando GeoJSON:", response.status_code)
    print("Alternativa: descarga https://datos.cdmx.gob.mx/dataset/catalogo-de-colonias-datos-abiertos/resource/026b42d3-a609-44c7-a83d-22b2150caffc/download/catalogo-colonias.geojson y usa with open()")
    exit()

geojson_data = response.json()
print("Colonias en GeoJSON:", len(geojson_data['features']))

m = folium.Map(location=[19.4326, -99.1332], zoom_start=11, tiles='CartoDB positron')

def get_color(grado):
    grado = str(grado).title()
    if 'Muy Alto' in grado or 'Muy alto' in grado:
        return '#8B0000'
    elif 'Alto' in grado:
        return '#FF4500'
    elif 'Medio' in grado:
        return '#FFA500'
    elif 'Bajo' in grado:
        return '#FFD700'
    elif 'Muy Bajo' in grado or 'Muy bajo' in grado:
        return '#90EE90'
    else:
        return '#D3D3D3'

def style_function(feature):
    nombre_geo_raw = feature['properties'].get('nom_col', '')
    nombre_geo = str(nombre_geo_raw).strip().upper() \
        .replace(r'^COL\.?\s*', '', regex=True) \
        .replace(r'^COLONIA\s*', '', regex=True) \
        .replace(r'^AMPL\s*', '', regex=True) \
        .replace(r'^AMPLIACION\s*', '', regex=True) \
        .replace(r'^AMP\s*', '', regex=True) \
        .replace(r'\s+', ' ', regex=True) \
        .replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U') \
        .replace('Ñ', 'N')

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
    name='Colonias CDMX - Marginación',
    style_function=style_function,
    tooltip=GeoJsonTooltip(
        fields=['nom_col'],
        aliases=['Colonia:'],
        sticky=True,
        style="font-size: 12px; background-color: white; border: 1px solid gray;"
    )
).add_to(m)

legend_html = '''
<div style="position: fixed; bottom: 50px; left: 50px; width: 240px; height: 200px; 
     border:2px solid grey; z-index:9999; font-size:14px; background-color:white; 
     padding:10px; border-radius:5px; opacity:0.9;">
<b>Densidad del lumpenproletariat por marginación</b><br>
<i style="background:#8B0000">&nbsp;&nbsp;&nbsp;</i> Muy Alto<br>
<i style="background:#FF4500">&nbsp;&nbsp;&nbsp;</i> Alto<br>
<i style="background:#FFA500">&nbsp;&nbsp;&nbsp;</i> Medio<br>
<i style="background:#FFD700">&nbsp;&nbsp;&nbsp;</i> Bajo<br>
<i style="background:#90EE90">&nbsp;&nbsp;&nbsp;</i> Muy Bajo<br>
<i style="background:#D3D3D3">&nbsp;&nbsp;&nbsp;</i> Sin dato
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

matched = 0
unmatched_names = set()
for feature in geojson_data['features']:
    nombre_geo_raw = feature['properties'].get('nom_col', '')
    nombre_geo = str(nombre_geo_raw).strip().upper() \
        .replace(r'^COL\.?\s*', '', regex=True) \
        .replace(r'^COLONIA\s*', '', regex=True) \
        .replace(r'^AMPL\s*', '', regex=True) \
        .replace(r'^AMPLIACION\s*', '', regex=True) \
        .replace(r'^AMP\s*', '', regex=True) \
        .replace(r'\s+', ' ', regex=True) \
        .replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U') \
        .replace('Ñ', 'N')
    if not df[df['nombre_col'] == nombre_geo].empty:
        matched += 1
    else:
        unmatched_names.add(nombre_geo_raw)

print(f"Colonias matched: {matched} de {len(geojson_data['features'])} ({matched / len(geojson_data['features']) * 100:.1f}%)")
print("Ejemplos GeoJSON sin match (originales):", list(unmatched_names)[:10])

m.save('index.html')
print("Mapa generado como 'index.html'. Ábrelo en tu navegador.")
print("Si aún muchos grises, compara muestras de nombres y ajusta limpieza.")