
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
        print(str)
    
    #client = mqtt.Client()
    st.session_state['msg'] = "" #inicializar variável que vai receber as mensagens pelo mqtt
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("192.168.1.98", 1883, 60)
    client.loop_forever()

if 'mqttThread' not in st.session_state:
    st.session_state.mqttClient = mqtt.Client()
    st.session_state.mqttThread = th.Thread(target=MQTT_TH, args=[st.session_state.mqttClient])
    add_script_run_ctx(st.session_state.mqttThread)
    st.session_state.mqttThread.start()

ip = st.text_input('Insert your LANmic IP') #irá receber o ip do lanmic, é necessário clicar "enter"

# Start Acquisition
if st.button('Record Audio :microphone:'):
    st.session_state.mqttClient.publish("aaibproject/request", payload=ip) #vai enviar uma string com o ip, depois será usada para fazer a conexão ao LANmic
    st.session_state['msg']="recording" #ao enviar o pedido, automaticamente irá começar a gravar

# Tentativa de ter um botão para parar a aquisição
#if st.button('Stop Recording :octagonal_sign:'):
#    st.session_state.mqttClient.publish("aaibproject/request", payload="stop")

# Se a msg for recording, está a gravar. Posteriormente a isso, queremos que a mensagem seja nula, para receber uma nova mensagem com a classe ou se deu erro
if st.session_state['msg']=="recording":
    with st.spinner('Recording Audio...'):
        st.info("When the audio is recorded it will wait for the classification")
        time.sleep(5)
    st.session_state['msg']=""

# Mensagem de erro, tamanho do buffer
if st.session_state['msg'] == "error":    
    st.error('Recording error, try again')

# Palavra é "Computador" - mostra o víde do gesto e a palavra respetiva em baixo
if st.session_state['msg'] == "Computador":
    video_file = open('computador.mp4', 'rb')
    video_bytes = video_file.read()
    st.video(video_bytes)
    st.subheader('Word: Computador')

    
# Palavra é "Engenharia" - mostra o víde do gesto e a palavra respetiva em baixo
if st.session_state['msg'] == "Engenharia":
    video_file = open('engenharia.mp4', 'rb')
    video_bytes = video_file.read()
    st.video(video_bytes)
    st.subheader('Word: Engenharia')

    
# Palavra é "Sinal" - mostra o víde do gesto e a palavra respetiva em baixo
if st.session_state['msg'] == "Sinal":
    video_file = open('sinal.mp4', 'rb')
    video_bytes = video_file.read()
    st.video(video_bytes)
    st.subheader('Word: Sinal')

if st.session_state['msg'] == "None":    
    st.subheader('Word: None')
