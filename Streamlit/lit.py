import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import accifunc as af
import time


st.set_page_config(page_title="Mad Traffic AI", page_icon=":car:", layout="wide", initial_sidebar_state="expanded")

st.sidebar.header("Mad Traffic AI" + " :car:")
st.sidebar.write('Mad Traffic AI is an accident prediction model that uses Machine Learning to predict where an accident can occur in real time in Madrid.')
st.sidebar.write("---")
st.sidebar.write("How does it work? :point_right: [Link to my GitHub](https://github.com/Calbacho/Mad-Traffic)")
st.sidebar.write("---")
st.sidebar.write("by Rafael Calbacho")





st.write(':oncoming_automobile: Accidents prediction :oncoming_automobile:')

mapa1 = af.acci_map()
#display folium map
st1 = st_folium(mapa1 , width=800, height=500)

st.write('---')
st.write(':vertical_traffic_light: Live Traffic in Madrid :vertical_traffic_light:')

mapa2 = af.trafic_map()
#display folium map
st2 = st_folium(mapa2 , width=800, height=500)


st.write('---')
st.write(':umbrella_with_rain_drops: Live Meteorology Madrid :umbrella_with_rain_drops:')

mapa3 = af.meteo_map()
#display folium map
st3 = st_folium(mapa3 , width=800, height=500)



