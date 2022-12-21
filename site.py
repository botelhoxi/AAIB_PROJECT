
import streamlit as st
import json
import paho.mqtt.client as mqtt
import threading as th
from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx
from streamlit_autorefresh import st_autorefresh
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
        st.session_state['msg'] = str
    
    #client = mqtt.Client()
    st.session_state['msg'] = ""
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

if st.button('Stop Recording :octagonal_sign:'):
    st.session_state.mqttClient.publish("aaibproject/request", payload="stop")

if st.session_state['msg']=="recording":
    st.info('Recording Audio...')

if st.session_state['msg']=="done":    
    st.success('Done Recording!')
    st.info("Waiting for classification...")

#if st.session_state['msg'] == "result" :
#    st.success("Result received!")
#    time.sleep(2)

if st.session_state['msg'] == "Computador":
    video_file = open('computador.mp4', 'rb')
    video_bytes = video_file.read()
    st.video(video_bytes)
    st.subheader('Word: Computador')

if st.session_state['msg'] == "Engenharia":
    video_file = open('engenharia.mp4', 'rb')
    video_bytes = video_file.read()
    st.video(video_bytes)
    st.subheader('Word: Engenharia')

if st.session_state['msg'] == "Sinal":
    video_file = open('sinal.mp4', 'rb')
    video_bytes = video_file.read()
    st.video(video_bytes)
    st.subheader('Word: Sinal')

if st.session_state['msg'] == "Não":    
    st.subheader('Classe de rejeição')

if st.session_state['msg'] == "novo":    
    st.subheader('Erro na gravação, grave de novo')
