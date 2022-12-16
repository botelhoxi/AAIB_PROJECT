import csv
import streamlit as st
import pandas as pd
import json
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import paho.mqtt.client as mqtt
import threading as th
from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx
from streamlit_autorefresh import st_autorefresh
from csv import writer
import plotly.express as px
import librosa as lib
import librosa.display
import time

st.title('AAIB PROJECT 2022')
st.subheader('Project that provides a translation from spoken words to sign language')

st_autorefresh(interval=5000)  

#MQTT Thread Function
def MQTT_TH(client):   
    def on_connect(client, userdata, flags, rc):       
        client.subscribe("aaibproject/data")
 
    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        str = msg.payload.decode()
        st.session_state['word'] = str
        st.session_state['recording'] = False
    
    #client = mqtt.Client()
    st.session_state['word'] = ""
    st.session_state['recording'] = False
    st.session_state['waiting'] = True
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("mqtt.eclipseprojects.io", 1883, 60)
    client.loop_forever()

if 'mqttThread' not in st.session_state:
    st.session_state.mqttClient = mqtt.Client()
    st.session_state.mqttThread = th.Thread(target=MQTT_TH, args=[st.session_state.mqttClient])
    add_script_run_ctx(st.session_state.mqttThread)
    st.session_state.mqttThread.start()

# Start Acquisition
if st.button('Record Audio :microphone:'):
    st.session_state.mqttClient.publish("aaibproject/request", payload="start")
    st.session_state['recording'] = True
    st.session_state['waiting'] = True

if st.session_state['recording'] and st.session_state['waiting']:
    st.session_state['waiting'] = False
    with st.spinner('Recording Audio...'):
        time.sleep(5)

if st.session_state['recording'] and not st.session_state['waiting']:    
    st.info('Done Recording! Waiting for classification')

if st.session_state['word'] != "" and not st.session_state['recording']:
    st.success("Done!")
    time.sleep(2)

if st.session_state['word'] == "Computador" and not st.session_state['recording']:
    video_file = open('computador.mp4', 'rb')
    video_bytes = video_file.read()
    st.video(video_bytes)
    st.subheader('Word: Computador')

if st.session_state['word'] == "Engenharia" and not st.session_state['recording']:
    video_file = open('engenharia.mp4', 'rb')
    video_bytes = video_file.read()
    st.video(video_bytes)
    st.subheader('Word: Engenharia')

if st.session_state['word'] == "Sinal" and not st.session_state['recording']:
    video_file = open('sinal.mp4', 'rb')
    video_bytes = video_file.read()
    st.video(video_bytes)
    st.subheader('Word: Sinal')
