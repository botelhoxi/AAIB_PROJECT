import paho.mqtt.client as mqtt
import threading as th
import sounddevice as sd
from scipy.io.wavfile import write
import librosa as lib
import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import time
import socket
import struct
import threading

import warnings
warnings.filterwarnings('ignore')

data = np.array([],np.int16)
wavFile = "som.wav"
samplerate=22050

def get_data():
    global data
    
    #settings 
    host = "192.168.1.88" #ip address of the mobile
    port = 8080 #port associated to the iphost

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    
        s.connect((host, port))

        #First call return format
        buffer = s.recv(200)
        #Second call return format info until the 16 byte. Both sould be ignored
        buffer = s.recv(200)
                        
        start_time = time.time()
        while True:
            buffer = s.recv(2000)
            #print("Gravando")
            data = np.concatenate((data, np.frombuffer(buffer, dtype = np.int16, offset = 0)))

def get_class(wavfile):
    y, sr = lib.load(wavfile) 
    #extract the features
    mfcc=lib.feature.mfcc(y=y,sr=sr)
    mf6 = np.mean(mfcc[5])
    mf7 = np.mean(mfcc[6])
    mf11 = np.mean(mfcc[10])
    mf13 = np.mean(mfcc[12])
    mf15 = np.mean(mfcc[14])
    sample = np.array([mf6, mf7, mf11, mf13, mf15])
    #creating the classifier
    data = pd.read_excel('data.xlsx')
    modelo = SVC(kernel='linear') 
    modelo.fit(data[['mf6', 'mf7','mf11', 'mf13', 'mf15']], data['classe'])
    #make the prediction
    prediction = modelo.predict(sample.reshape(1, -1))
    #prediction = modelo.predict(sample[0])
    if(prediction == 1): classe = "Computador"
    elif(prediction == 2): classe = "Engenharia"
    elif(prediction == 3): classe = "Sinal"
    else: classe = "Não"
    return classe

def MQTT_TH(client):    
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc)) 
        #subscribing in on_connect() means that if we lose the connection and
        #reconnect then subscriptions will be renewed.
        #print("Received Message")
        client.subscribe("aaibproject/request") #subscrive to the request of adquiring the data
 
    #the callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        
        msg = str(msg.payload.decode())       
        print(msg)
        
        if msg == "start":
            x = threading.Thread(target=get_data)
            x.start()
            print(threading.active_count())
            client.publish("aaibproject/data", "recording")

        elif msg == "stop":
            client.publish("aaibproject/data", "done")
            write(wavFile, samplerate, data);   
            data = np.array([],np.int16)
            classe = get_class(wavFile) 
            client.publish("aaibproject/data", "result")
            client.publish("aaibproject/data", classe)

    print('Incializing MQTT')
    client.on_connect = on_connect
    client.on_message = on_message
  
    client.connect("mqtt.eclipseprojects.io", 1883, 60)
   
    client.loop_forever()
