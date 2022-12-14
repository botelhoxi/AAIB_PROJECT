import time
import json
import socket
import librosa
import scipy
import numpy as np
from flask import Flask, render_template
from flask_socketio import SocketIO
from scipy.io.wavfile import write
import pandas as pd
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn import datasets, metrics
import matplotlib.pyplot as plt
from threading import Thread, Event


app = Flask(__name__)
socketio = SocketIO(app)

thread = Thread()
thread_stop_event = Event()

# Sampling Frequency
Fs = 22050
AqTime = 5

def SaveFile(sr, data):
    try:
        npdata = np.frombuffer(data, dtype=np.int32)
        wavFile = 'audiofile' +'.wav'
        write(wavFile, sr, npdata)
        return True

    except Exception as e:
        socketio.emit('serverResponse', {'message': 'RecordingError', 'error': 'bufferSize'})
        print(e)
        return False


def WavPostprocessing(sr = 11025, ts = 0.5, debug = True):
    """
    Reads and operates over the .wav file as to locate and extract the audio slice containing the word.

    Parameters
    ----------
    (int) fs - Sampling Frequency used in LanMic
    (float) ts - Number of initial seconds to be removed from the original audio (helps removing Metadata information)
    (bool) debug - If true saves a pdf containing the region of the original wave selected by the algorithm as being the word section
    
    Returns
    -------
    (array) trim - A array corresponding to the word slice selected by the algorithm.  
    """
    # Read the audio file and remove the first 0.5 seconds of signal corresponding to metadata
    data_path = 'recordings/Luis1.wav'

    # Load audio data
    sr = 11025
    arr, *_ = librosa.load(data_path, sr = sr)

    # Remove the metadata section
    junk = int(sr * 0.5)
    arr = arr[junk:]
    
    # -------------- Word detection ----------------

    # Audio Split function parameters
    max_dB = 40 
    frame_len = 1024
    hop_len = 100

    # Anything below max_db - top_db(max-dB) is labeled as silence
    none_mute_sections = librosa.effects.split(arr, top_db = max_dB, frame_length = frame_len, hop_length= hop_len)

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
        fig.savefig('audiofile.pdf')
    print("Hello")
    return arr[start_index:end_index]

def ExtractFeatures(wave, fs):
    # Features extraction and classification

    # Statistical Features
    freqs = np.fft.fftfreq(wave.size) # Compute the frequency associated with coefficients
    f_q3 = np.quantile(freqs, 0.75) # Compute the third quartile (75%)
    f_iqr = scipy.stats.iqr(freqs)# Compute the interquartile range

    # Spectral Features
    mfccs = librosa.feature.mfcc(wave, sr=fs)

    # Add all features to a single array
    features = np.array([f_q3, f_iqr, np.mean(mfccs[2]), np.mean(mfccs[5]), np.mean(mfccs[6])], dtype = 'float')

    return features

def SupportVectorClassifier(features):
    
    path_svm = 'classifier_svm.csv'
    df = pd.read_csv(path_svm, dtype = {'y': str, 'f_q3': float, 'f_iqr': float, 'mfcc3': float, 'mfcc6': float, 'mfcc7': float})

    # Convert dataframe to numpy to an numpy array as to improve computation speed
    x_train = df.values[:,1:]
    y_train = df.values[:,0]
    
    svm = make_pipeline(StandardScaler(), SVC(kernel = 'rbf', gamma='scale'))
    svm.fit(x_train, y_train)

    # reshape is needed since predict expects a matrix(n_samples, n_features)
    prediction = svm.predict(features.reshape(1, -1))
    
    return prediction[0]

def soundRecording():   
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            
            # Streaming device Ip and Port
            host = "192.168.0.205"
            port = 8080
            try:
                # Debug: print('Opening socket')
                s.connect((host, port))
                
                chunk_size = 1024 
                samplerate = 11025 
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
                saved = SaveFile(samplerate, data)
                if(saved):
                    
                    # Send Confirmation of end of recording
                    #socketio.emit('serverResponse', {'message': 'RecordingEnded'})
            
            except Exception as e:
                socketio.emit('serverResponse', {'message': 'RecordingError', 'error': 'deviceCon'})
                print(e)
                s.close()
    


# ------------- SERVER HANDLING --------------------

@app.route('/')
def sessions():
    return render_template('main.html')


@socketio.on('connect')
def handle_connect():
    socketio.emit('serverResponse', {'message': 'Client connected'})


@socketio.on('request')
def handle_request(req):

    # Decode the sent JSON
    decoded = json.loads(req)
    if decoded['request'] == 'startRecording':
        global thread
        thread = socketio.start_background_task(soundRecording)

    if decoded['request'] == 'stopRecording':
        #Should Stop data streaming
        thread_stop_event.set()
        thread.join()
        thread_stop_event.clear()   

    if decoded['request'] == 'guessPerson':
        
        # Extract the features from the collected audio file
        features = ExtractFeatures(WavPostprocessing(debug = True), fs = 11025)
        #print(features)

        # Get the classifier prediction
        prediction = SupportVectorClassifier(features)

        # Send Prediction Result
        socketio.emit('serverResponse', {'message': 'PredictionDone', 'prediction': prediction})
        

if __name__ == '__main__':
    socketio.run(app, debug=True)
