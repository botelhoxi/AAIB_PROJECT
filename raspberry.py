import paho.mqtt.client as mqtt
import threading as th
from scipy.io.wavfile import write
import librosa as lib
import numpy as np
import pandas as pd
from sklearn.svm import SVC
import time
import socket
import matplotlib.pyplot as plt

# Grava audio a partir do ip que foi recebido pelo mqtt, introduzido pelo 
# utilizador no streamlit
def get_data(host):
    
    global samplerate
    wavFile = "som.wav"
    AqTime = 5

    # Configurações 
    samplerate = 22050 # Taxa de aquisição escolhida no LANmic
    port = 8080 # Port associado ao IP (é sempre 8080)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    
        s.connect((host, port))

        chunk_size = 1024
        samplerate = int(samplerate/2)    #  Sample Rate/2

        # Esperar os dados serem adquiridos antes do inicio
        time.sleep(chunk_size/samplerate)
        data=s.recv(chunk_size)
        t0=time.time()
        # Adquirir pelo periodo de tempo = AqTime = 5s
        while time.time()-t0 < AqTime:           
            time.sleep(chunk_size/samplerate/4)
            data+=s.recv(chunk_size)
            # "Flush" o buffer
        time.sleep(0.2)
        data+=s.recv(chunk_size)
        
        # Costuma dar erro "buffer size must be a multiple of element size",
        # tentar correr o seguinte código, se não der retorna erro que depois
        # vai ser enviado para o streamlit
        try:
            npdata=np.frombuffer(data, dtype=np.int32)
            write(wavFile, samplerate, npdata); 
            return wavFile         
        except:
            return "erro"   
  
        # Fechar socket
        s.close()  
         
def extract_word(debug=False):

    # Read the audio file and remove the first 0.5 seconds of signal corresponding to metadata
    data_path = 'som.wav'
    # Load audio data
    sr = 22050
    arr, *_ = lib.load(data_path, sr = sr)

    # Remove the metadata section
    junk = int(sr * 0.5)
    arr = arr[junk:]

    # -------------- Word detection ----------------

    # Audio Split function parameters
    max_dB = 40 
    frame_len = 1024
    hop_len = 100

    # Anything below max_db - top_db(max-dB) is labeled as silence
    none_mute_sections = lib.effects.split(arr, top_db = max_dB, frame_length = frame_len, hop_length= hop_len)

    # Find the section with the highest mean amplitude (corresponding to the word)
    row = 0
    max_m = 0
    for n, section in enumerate(none_mute_sections):
        mean = np.mean(np.abs(arr[section[0]:section[1]]))
        if mean > max_m:
            max_m = mean
            row = n

    # Extract the word section
    start_index = none_mute_sections[row,0]
    end_index = none_mute_sections[row,1]

    # For Debugging purposes -> Wave visualization
    if debug:
        t = np.arange(0, len(arr)/sr, 1/sr)
        t2 = np.arange(start_index/sr, end_index/sr, 1/sr) 
        fig = plt.figure()
        plt.plot(t, arr)

        if t2.shape != arr[start_index:end_index].shape:
            plt.plot(t2[:-1], arr[start_index:end_index])
        else:
                plt.plot(t2, arr[start_index:end_index])

    #fig.savefig('audiofile.pdf')
    return arr[start_index:end_index]
    
def get_class(som):
    # Extrair features
    mfcc=lib.feature.mfcc(y=som,sr=samplerate)
    mf5 = np.mean(mfcc[4])
    zero_crossings = sum(lib.zero_crossings(som, pad=False))
    mf9 = np.mean(mfcc[8])
    mf14 = np.mean(mfcc[13])
    sample = np.array([mf5, zero_crossings, mf9, mf14])
    # Criar o classificador
    data = pd.read_excel('data.xlsx')
    modelo = SVC(kernel='linear') 
    modelo.fit(data[['mf5', 'zero_crossings', 'mf9', 'mf14']], data['classe'])
    # Fazer a prediction
    prediction = modelo.predict(sample.reshape(1, -1))
    if(prediction == 1): classe = "Computador"
    elif(prediction == 2): classe = "Engenharia"
    elif(prediction == 3): classe = "Sinal"
    else: classe = "None"
    return classe

#MQTT Thread Function
def MQTT_TH(client):    
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc)) 
        #subscribing in on_connect() means that if we lose the connection and
        #reconnect then subscriptions will be renewed.
        client.subscribe("aaibproject/request") #subscrive to the request of adquiring the data
 
    #the callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        msg = str(msg.payload.decode())
        print(msg)
        print("Recording")
        msg = get_data(msg) #get the name of the recorded audio, after it's finishing recording
      
        # Se for mensagem de erro, enviar para o streamlit logo
        if msg == "erro":
            print("Recording Error")
            client.publish("aaibproject/data", "error") 
        
        # Caso não dê erro, classificar e enviar a classe
        else:
            som = extract_word()
            classe = get_class(som)
            print(classe)
            client.publish("aaibproject/data", classe)

    print('Incializing MQTT')
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("mqtt.eclipseprojects.io", 1883, 60) 
    client.loop_forever()

# Criar Thread
t = th.Thread(target=MQTT_TH, args=[mqtt.Client()])
t.start()
