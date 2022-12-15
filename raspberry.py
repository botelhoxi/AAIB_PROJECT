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

fs = 44100 #sampling frequency, will be a parameter in the function responsible for recording the audio
second = 4 #defines the duration of the recorded audio

#MQTT Thread Function

def get_class(wavfile):
    #record_voice = sd.rec( int( second * fs ) , samplerate = fs , channels = 2 )
    #sd.wait() # wait for the recording of the audio to continue with the script
    #write("som.wav", fs , record_voice )
    y, sr = lib.load(wavfile) 
    # EXTRAIR AS FEATURES
    mfcc=lib.feature.mfcc(y=y,sr=sr)
    mf6 = np.mean(mfcc[5])
    mf7 = np.mean(mfcc[6])
    mf11 = np.mean(mfcc[10])
    mf13 = np.mean(mfcc[12])
    mf15 = np.mean(mfcc[14])
    sample = np.array([mf6, mf7, mf11, mf13, mf15])
    # CLASSIFICADOR
    data = pd.read_excel('data.xlsx')
    modelo = SVC(kernel='linear') 
    modelo.fit(data[['mf6', 'mf7','mf11', 'mf13', 'mf15']], data['classe'])
    # FAZER A PREDICTION
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
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        print("Recebi")
        client.subscribe("aaibproject/request") #subscrive to the request of adquiring the data
 
    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))   
        wavfile = get_data()
        class = get_class(wavfile) # get the data from the function
        #print(classe)
        print("Publiquei")
        client.publish("aaibproject/data", class)

    print('Incializing MQTT')
    client.on_connect = on_connect
    client.on_message = on_message
  
    client.connect("mqtt.eclipseprojects.io", 1883, 60)
   
    client.loop_forever()

t = th.Thread(target=MQTT_TH, args=[mqtt.Client()])
t.start()
