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
import matplotlib.pyplot as plt


fs = 44100 #sampling frequency, will be a parameter in the function responsible for recording the audio
second = 4 #defines the duration of the recorded audio
gravar = False
#MQTT Thread Function
def get_data(client, host):
    global gravar
    #print ('The begin (lanmic)...') #marks the begin of the function

    #wavFile = input('Wav filename: ') #requests the name of the file, not needed because we only want the ML result, not to hear de audio
    #wavFile = wavFile +'.wav' #wav format
    wavFile = "som.wav"
    
    #AqTime = int(input('Aquisition time (s): ')) #requests the aquisition time, we will try with 5s default and maybe after we can get the time by the streamlit
    AqTime = 5

    #settings 
    #host = "192.168.1.5" #ip address of the mobile
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
        client.publish("aaibproject/data", "recording")
        #wait for data to be aquired before start
        time.sleep(chunk_size/samplerate)
        data=s.recv(chunk_size)
        t0=time.time()
        #aquire for a period of time
        while gravar == True:           
            time.sleep(chunk_size/samplerate/4)
            data+=s.recv(chunk_size)
            # to flush the buffer
        time.sleep(0.2)
        data+=s.recv(chunk_size)
        print("PAROU")
        #print('... finished')
    
        #l=len(data)
        #print('Length of data (3)= ', l)
   
        #Convert to numpy array
        
        npdata=np.frombuffer(data, dtype=np.int32)
        s.close() 
        write(wavFile, samplerate, npdata); 
        
        print('wav file writeen\n')
        #return wavFile    
        
        #except:
        #    print("erro")
        #    return "erro"
  
        
    
        #close socket
          
        #print('socket closed') 
        
def extract_word():
    debug=True
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
    return arr[start_index:end_index], sr

def get_class(som, sr, client):
    client.publish("aaibproject/data", "done")
    y, sr = lib.load("som.wav") 
    #extract the features
    mfcc=lib.feature.mfcc(y=som,sr=sr)
    mf2 = np.mean(mfcc[1])
    mf4 = np.mean(mfcc[3])
    mf9 = np.mean(mfcc[8])
    sample = np.array([mf2, mf4, mf9])
    #creating the classifier
    data = pd.read_excel('data.xlsx')
    modelo = SVC(kernel='linear') 
    modelo.fit(data[['mf2', 'mf4','mf9']], data['classe'])
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
        msg = str(msg.payload.decode())
        global gravar
        if(msg == "stop"):
            gravar = False
            som, sr = extract_word()
            classe = get_class(som, sr, client) #get the class from the audio acquired
            print(classe)
            client.publish("aaibproject/data", classe) 
        else:            
            gravar = True
            #get_data(client, msg)
            s = th.Thread(target = get_data, args=[client, msg])
            s.start()

    print('Incializing MQTT')
    client.on_connect = on_connect
    client.on_message = on_message
  
    client.connect("mqtt.eclipseprojects.io", 1883, 60)
   
    client.loop_forever()

t = th.Thread(target=MQTT_TH, args=[mqtt.Client()])
t.start()