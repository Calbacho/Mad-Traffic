def get_live_traffic():

    import pandas as pd
    import numpy as np
    import requests
    import xml.etree.ElementTree as ET
    import utm

    url = 'https://informo.madrid.es/informo/tmadrid/pm.xml'

    response = requests.get(url)

    root = ET.fromstring(response.content)

    fecha = []
    hora = []

    fech = root.find('fecha_hora').text.split(' ')[0]
    hor = root.find('fecha_hora').text.split(' ')[1]

    idelem = []
    intensidad = []
    ocupacion = []
    carga = []
    x_utm = []
    y_utm = []
    latitude = []
    longitude = []


    for i in root.findall('pm'):

        fecha.append(fech)
        hora.append(hor)
        idelem.append(i.find('idelem').text)
        intensidad.append(i.find('intensidad').text)
        ocupacion.append(i.find('ocupacion').text)
        carga.append(i.find('carga').text)
        x_utm.append(i.find('st_x').text.split(',')[0])
        y_utm.append(i.find('st_y').text.split(',')[0])

        x = float(i.find('st_x').text.replace(',', '.'))
        y = float(i.find('st_y').text.replace(',', '.'))

        lat, lon = utm.to_latlon(x, y, 30, 'T')

        latitude.append(lat)
        longitude.append(lon)

    live = pd.DataFrame({'fecha': fecha, 'hora': hora, 'idelem': idelem, 'intensidad': intensidad, 'ocupacion': ocupacion, 'carga': carga, 'x_utm': x_utm, 'y_utm': y_utm, 'latitude': latitude, 'longitude': longitude})

    # transform dataframe columns to appropriate types

    live['fecha'] = pd.to_datetime(live['fecha'])
    live['idelem'] = live['idelem'].astype(int)
    live['intensidad'] = live['intensidad'].astype(int)
    live['ocupacion'] = live['ocupacion'].astype(int)
    live['carga'] = live['carga'].astype(int)
    live['x_utm'] = live['x_utm'].astype(int)
    live['y_utm'] = live['y_utm'].astype(int)

    #merge with geo_live

    geo_live = pd.read_csv('../data/geo_live.csv')

    live = pd.merge(live, geo_live[['idelem', 'idema']], on='idelem')

    #get data for meteo

    url2 = 'https://opendata.aemet.es/opendata/api/observacion/convencional/todas'

    querystring = {"api_key":"eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJjYWxiYWNob3JhZmFAZ21haWwuY29tIiwianRpIjoiZGYxY2NmYjMtODUwNS00ZThmLWFkNDMtZThhNmNjZTM2MzRmIiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE2Nzg0MDYzMzAsInVzZXJJZCI6ImRmMWNjZmIzLTg1MDUtNGU4Zi1hZDQzLWU4YTZjY2UzNjM0ZiIsInJvbGUiOiIifQ.aSYqe-UW9wGT34RqhFbvzTN2UJ7SbwZWCLQFFFtJLPc"}

    headers = {
        'cache-control': "no-cache"
    }

    response = requests.request("GET", url2, headers=headers, params=querystring)

    data = requests.request("GET", response.json()['datos'], headers=headers, params=querystring)

    data = pd.DataFrame(data.json())

    data = data[['idema', 'prec', 'vv']].groupby('idema').last().reset_index()

    live = pd.merge(live, data, on='idema')

    live = live[['fecha', 'hora', 'idelem', 'intensidad', 'ocupacion', 'carga','prec', 'vv', 'x_utm', 'y_utm', 'latitude', 'longitude']]

    return live

def trafic_map():

    import folium
    from folium.plugins import HeatMap
    import pandas as pd

    madrid1 = folium.Map(location=[40.416775, -3.703790], zoom_start=12)

    live = get_live_traffic()

    # Create a list of lists that contains the latitude, longitude, and intensity values
    data = [[row['latitude'], row['longitude'], row['carga']] for index, row in live.iterrows()]

    # Create the heatmap layer
    HeatMap(data=data, min_opacity=0.25, radius=11, blur=15, max_zoom=1, gradient={0.4: 'green', 0.6: 'orange', 1: 'red'}).add_to(madrid1)

    return madrid1




# Generate map from acci_prob function

def direccion(lat, lon):

    from geopy.geocoders import Nominatim

    geolocator = Nominatim(user_agent="myGeocoder")

    location = geolocator.reverse(f"{lat}, {lon}")

    #get street name

    street = location.raw['address']['road']

    #get street number

    try:
        number = location.raw['address']['house_number']
    except:
        number = ''

    #get city

    city = location.raw['address']['city']

    #get postal code

    postal = location.raw['address']['postcode']

    #return address

    dir = f"{street} {number}, {postal}, {city}"

    return dir



def acci_prob():

    import pandas as pd
    import numpy as np
    import pickle
    import warnings

    warnings.filterwarnings('ignore')
    
    prueba = get_live_traffic()

    prueba['mes'] = prueba.fecha.astype(str).str[5:7]
    prueba['dia_semana'] = prueba.fecha.dt.dayofweek.astype(str)
    prueba['hora'] = (pd.to_datetime(prueba['hora'], format='%H:%M:%S') - pd.to_timedelta(pd.to_datetime(prueba['hora'], format='%H:%M:%S').dt.minute % 30, unit='m')).dt.strftime('%H:%M:%S').str[:-2] + '00'
    prueba.drop(['fecha', 'x_utm', 'y_utm', 'latitude', 'longitude'], axis=1, inplace=True)

    #change column name of vv to velmedia

    prueba.rename(columns={'vv': 'velmedia'}, inplace=True)

    prueba_dum = pd.get_dummies(prueba, columns=['mes', 'dia_semana', 'hora'])

    prueba_dum.idelem = prueba_dum.idelem.astype(str)

    train_vacia = pd.read_csv('../data/train_vacia.csv')

    train = pd.concat([train_vacia, prueba_dum], axis=0).fillna(0)

    train['prob'] = 0

    train.intensidad = train.intensidad.astype(float)
    train.ocupacion = train.ocupacion.astype(float)
    train.carga = train.carga.astype(float)
    train.prob = train.prob.astype(float)

    cols_to_convert = train.columns.difference(['idelem', 'intensidad', 'ocupacion', 'carga', 'prec', 'velmedia'])

    train[cols_to_convert] = train[cols_to_convert].astype('uint8')

    for i in train.idelem.unique():

        try:

            filename = 'modelo_' + i + '.sav'

            modelo = pickle.load(open('../modelos_svm/' + filename, 'rb'))

            train.loc[train.idelem == i, 'prob'] = 1 - modelo.predict_proba(train.loc[train.idelem == i, :].drop(['prob', 'idelem'], axis=1))[0].max()

        except:

            train.loc[train.idelem == i, 'prob'] = 0

    geo = pd.read_csv('../data/geo_live.csv')

    geo.idelem = geo.idelem.astype(str)

    train_final = pd.merge(train[['idelem', 'prob']], geo[['idelem', 'latitud', 'longitud']], on='idelem', how='left')

    return train_final.sort_values('prob', ascending=False)



def meteo_map():

    import folium
    from folium.plugins import HeatMap
    import pandas as pd

    madrid2 = folium.Map(location=[40.416775, -3.703790], zoom_start=12)

    live = get_live_traffic()

    # Create a list of lists that contains the latitude, longitude, and intensity values
    data = [[row['latitude'], row['longitude'], row['prec']] for index, row in live.iterrows()]

    # Create the heatmap layer
    HeatMap(data=data, min_opacity=0.25, radius=14, blur=15, max_zoom=1, gradient={0.4: 'green', 0.6: 'orange', 1: 'red'}).add_to(madrid2)

    return madrid2


def acci_map():

    import folium
    from folium.plugins import HeatMap
    from folium.features import DivIcon
    import pandas as pd


    acci = acci_prob()

    madrid3 = folium.Map(location=[40.416775, -3.703790], zoom_start=12)

    #heatmap

    data = [[row['latitud'], row['longitud'], row['prob']] for index, row in acci.iterrows()]

    HeatMap(data=data, min_opacity=0.25, radius=15, blur=15, max_zoom=1, gradient={0.1: 'green', 0.4: 'orange', 0.7: 'red'}).add_to(madrid3)

    for i in range(5):

        folium.CircleMarker(location=[acci.iloc[i]['latitud'], acci.iloc[i]['longitud']],
                            radius=10,
                            color='red',
                            fill=True,
                            fill_color='red',
                            label=round(acci.iloc[i]['prob']*100,2)).add_to(madrid3)

        

        
        folium.Marker(location=[acci.iloc[i]['latitud'], acci.iloc[i]['longitud']], 
                    icon=DivIcon(icon_size=(30,30),
                                icon_anchor=(15,-5),
                                html=f'<div style="font-size: 14pt">%s</div>' % str(str(round(acci.iloc[i]['prob']*100,2))+'%')),
                    popup=direccion(acci.iloc[i]['latitud'], acci.iloc[i]['longitud']),
                    tooltip=False,).add_to(madrid3)

    return madrid3





