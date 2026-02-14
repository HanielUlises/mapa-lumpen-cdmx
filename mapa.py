import folium
import pandas as pd
import requests
from folium.features import GeoJsonTooltip

df = pd.read_csv('marginacion_cdmx.csv', encoding='utf-8')

df['codigo_postal'] = (
    df['código postal']
    .astype(str)
    .str.strip()
    .str.zfill(5)
)

df['grado'] = (
    df['grado de marginación']
    .astype(str)
    .str.strip()
    .str.title()
)

orden_grado = {
    'Muy Bajo': 1,
    'Bajo': 2,
    'Medio': 3,
    'Alto': 4,
    'Muy Alto': 5
}

df['orden'] = df['grado'].map(orden_grado)

df_cp = (
    df.groupby('codigo_postal', as_index=False)
      .agg({'orden': 'max'})
)

inv_orden = {v: k for k, v in orden_grado.items()}
df_cp['grado'] = df_cp['orden'].map(inv_orden)

geojson_url = "https://raw.githubusercontent.com/open-mexico/mexico-geojson/main/09-Cdmx.geojson"
geojson_data = requests.get(geojson_url).json()

m = folium.Map(
    location=[19.4326, -99.1332],
    zoom_start=11,
    tiles='CartoDB positron'
)

def get_color(grado):
    if grado == 'Muy Alto':
        return '#8B0000'
    elif grado == 'Alto':
        return '#FF4500'
    elif grado == 'Medio':
        return '#FFA500'
    elif grado == 'Bajo':
        return '#FFD700'
    elif grado == 'Muy Bajo':
        return '#90EE90'
    else:
        return '#D3D3D3'

def style_function(feature):
    cp_geo = str(feature['properties'].get('d_codigo', '')).strip().zfill(5)
    match = df_cp[df_cp['codigo_postal'] == cp_geo]

    if not match.empty:
        grado = match['grado'].iloc[0]
        opacity = 0.75
    else:
        grado = 'Sin dato'
        opacity = 0.1

    return {
        'fillColor': get_color(grado),
        'color': '#444444',
        'weight': 0.3,
        'fillOpacity': opacity
    }

folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=GeoJsonTooltip(
        fields=['d_codigo'],
        aliases=['C.P.:'],
        sticky=True,
        style="font-size: 13px; background: white; padding: 6px; border-radius: 4px;"
    )
).add_to(m)

legend_html = '''
<div style="position: fixed; bottom: 50px; left: 50px; width: 300px; 
     border:2px solid #333; z-index:9999; font-size:14px; background:#f9f9f9; 
     padding:15px; border-radius:4px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); 
     opacity:0.95; font-family: Arial, sans-serif; line-height:1.6;">
<b>Densidad del lumpenproletariat</b><br><br>
<span style="color:#8B0000; font-weight:bold;">■ Muy Alto</span><br>
<span style="color:#FF4500; font-weight:bold;">■ Alto</span><br>
<span style="color:#FFA500; font-weight:bold;">■ Medio</span><br>
<span style="color:#FFD700; font-weight:bold;">■ Bajo</span><br>
<span style="color:#90EE90; font-weight:bold;">■ Muy Bajo</span><br>
<span style="color:#D3D3D3; font-weight:bold;">■ Sin dato</span>
</div>
'''

m.get_root().html.add_child(folium.Element(legend_html))
m.save('index.html')
