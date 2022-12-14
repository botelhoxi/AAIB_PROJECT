# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import threading as th
import sounddevice as sd
from scipy.io.wavfile import write
import librosa as lib
import numpy as np
import pandas as pd
import time
import socket
from sklearn.svm import SVC

#fs = 44100 #sampling frequency, will be a parameter in the function responsible for recording the audio
#second = 4 #defines the duration of the recorded audio

#MQTT Thread Function
def get_data():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            
            # Streaming device Ip and Port
            host = "10.22.103.254"
            port = 8080
            try:
                # Debug: print('Opening socket')
                s.connect((host, port))
                
                chunk_size = 1024 
                samplerate = 44100 
                # Send Confirmation of device connection
                #socketio.emit('serverResponse', {'message': 'RecordingStarted'})
                
                #wait for data to be aquired before start
                time.sleep(chunk_size/samplerate)
                data = s.recv(chunk_size)
                t0 = time.time()
                
                #record sound
                while not thread_stop_event.isSet():
                    time.sleep(chunk_size/samplerate/4)
                    data = data + s.recv(chunk_size)
                
                # to flush the buffer
                time.sleep(0.2)
                data = data + s.recv(chunk_size)

                # Debug: print('Closing socket')
                s.close()
		
                # Save the audio file
                
                npdata = np.frombuffer(data, dtype=np.int32)
                wavFile = 'audiofile' +'.wav'
                write(wavFile, samplerate, npdata)
                return wavFile
                    #return True

                #except Exception as e:
                #    socketio.emit('serverResponse', {'message': 'RecordingError', 'error': 'bufferSize'})
                #    print(e)
                #    return False
                #if(saved):
                    
                    # Send Confirmation of end of recording
                    #socketio.emit('serverResponse', {'message': 'RecordingEnded'})
            
            except Exception as e:
                #socketio.emit('serverResponse', {'message': 'RecordingError', 'error': 'deviceCon'})
                print(e)
                s.close()

def get_class(audio):
    record_voice = sd.rec( int( second * fs ) , samplerate = fs , channels = 2 )
    sd.wait() # wait for the recording of the audio to continue with the script
    write("som.wav", fs , record_voice )
    y, sr = lib.load(audio) 
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
        print("Recebi")
        client.subscribe("aaibproject/request") #subscrive to the request of adquiring the data
 
    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        print(msg.topic+" "+str(msg.payload)) 
        data = get_data()
        gloval v
        if msg = start:
            v = true
        classe = get_class(data) 
        print("Publiquei")
        client.publish("aaibproject/data", classe)

    print('Incializing MQTT')
    client.on_connect = on_connect
    client.on_message = on_message
  
    client.connect("mqtt.eclipseprojects.io", 1883, 60)
   
    client.loop_forever()

t = th.Thread(target=MQTT_TH, args=[mqtt.Client()])
t.start()