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

st.title('Cloud Logger - AAIB 2022')

with st.sidebar:
    add_radio = st.radio(
        "Tabela de conteudos",
        ("Introdução", "Iniciar aquisição")
    )

st_autorefresh(interval=5000)  

#MQTT Thread Function
def MQTT_TH(client):   
    def on_connect(client, userdata, flags, rc):       
        client.subscribe("aaibproject/data")
 
    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        print("Recebi")
        str = msg.payload.decode()
        print(type(str))
        print(str) 
    
    #client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("mqtt.eclipseprojects.io", 1883, 60)
    client.loop_forever()

if 'mqttThread' not in st.session_state:
    st.session_state.mqttClient = mqtt.Client()
    st.session_state.mqttThread = th.Thread(target=MQTT_TH, args=[st.session_state.mqttClient])
    add_script_run_ctx(st.session_state.mqttThread)
    st.session_state.mqttThread.start()

# Botão
if add_radio == 'Iniciar aquisição':
    st.session_state.mqttClient.publish("aaibproject/request", payload="start")
    print("Enviei")

else:
    st.graphviz_chart('''
        digraph {
            subgraph {
                microfone -> computador
            computador -> mqtt_dados [color=blue, style=dotted, shape=box]
            mqtt_dados -> gitpod [color=blue, style=dotted]
            mqtt_pedido -> computador [color=blue, style=dotted]
            gitpod -> mqtt_pedido [color=blue, style=dotted]        
            mqtt_pedido  [shape=box]
            mqtt_dados  [shape=box]
            rank = same; mqtt_pedido; mqtt_dados;
            }
        }
    ''')
    st.caption('O diagrama acima é uma generalização do funcionamento da aplicação feito com recurso ao graphviz')
    st.text('Esta página web é o resultado do projeto "Cloud Logger de instrumentação"\nrealizado na cadeira de Aplicações Avançadas em Instrumentação Biomédica.')
    st.text('Esta página web tem duas opções apresentadas na barra lateral à esquerda.\nA primeira, na qual se encontra neste momento, contém uma rápida introdução\ne explicação do funcionamento da aplicação.')
    st.subheader('Introdução')
    st.text('Esta página web configurada no gitpod comunica com um computador pessoal através do\nprotocolo de comunição MQTT.\nQuando selecionada a opção "Iniciar aquisição" da barra lateral é enviado pela Cloud\num pedido de gravação de dados ao computador local que utiliza o microfone embebido\npara gravar um ficheiro .wav.\nNa mesma máquina em que é gravado o ficheiro de som, são também calculadas\ncaracterísticas do som que são então enviadas pela CLoud para serem apresentadas\nnesta página web.\nEnquanto a opção de aquisição está selecionada a comunicação é feita continua\ne sequencialmente, havendo um pedido de gravação a cada 5 segundos seguido do\nenvio e atualização dos gráficos na página web\nHá também a possibilidade de guardar os dados mostrados em gráfico num ficheiro .csv\nonde são guardados todos os instantes desde o inicio da aquisição.')
