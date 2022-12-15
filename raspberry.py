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
def get_data():
    
    #print ('The begin (lanmic)...') #marks the begin of the function

    #wavFile = input('Wav filename: ') #requests the name of the file, not needed because we only want the ML result, not to hear de audio
    #wavFile = wavFile +'.wav' #wav format
    wavFile = "som.wav"
    
    #AqTime = int(input('Aquisition time (s): ')) #requests the aquisition time, we will try with 5s default and maybe after we can get the time by the streamlit
    AqTime = 5

    #settings 
    host = "192.168.1.155" #ip address of the mobile
    samplerate = 22050 #(LANmic sample rate)
    port = 8080 #port associated to the iphost

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    
        #print('Opening socket') #marks the begin of socket
        s.connect((host, port))

        chunk_size = 1024 # 512
        #audio_format = pyaudio.paInt16
        channels = 1
        #samplerate = 22050 #(LANmic sample rate /2)
        samplerate = int(samplerate/2)    #(LANmic sample rate /2)

        #print('connected to server\n')
        #print('Sound being aquired ...')
    
        #wait for data to be aquired before start
        time.sleep(chunk_size/samplerate)
        data=s.recv(chunk_size)
        t0=time.time()
        #aquire for a period of time
        while time.time()-t0 < AqTime:           
            time.sleep(chunk_size/samplerate/4)
            data+=s.recv(chunk_size)
            # to flush the buffer
        time.sleep(0.2)
        data+=s.recv(chunk_size)
   
        #print('... finished')
    
        #l=len(data)
        #print('Length of data (3)= ', l)
   
        #Convert to numpy array
        npdata=np.frombuffer(data, dtype=np.int32)
  
        #save data   
        write(wavFile, samplerate, npdata);     
        print('wav file writeen\n')
    
        #close socket
        s.close()   
        #print('socket closed') 
        return wavFile

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
        print("Received")
        client.subscribe("aaibproject/request") #subscrive to the request of adquiring the data
 
    #the callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))   
        wavfile = get_data() #get the name of the recorded audio, after it's finishing recording
        classe = get_class(wavfile) #get the class from the audio acquired
        #print(classe)
        print("Publish")
        client.publish("aaibproject/data", classe)

    print('Incializing MQTT')
    client.on_connect = on_connect
    client.on_message = on_message
  
    client.connect("mqtt.eclipseprojects.io", 1883, 60)
   
    client.loop_forever()

t = th.Thread(target=MQTT_TH, args=[mqtt.Client()])
t.start()
