import RPi.GPIO as GPIO
import serial
import os
import time
import matplotlib.pyplot as plt
import numpy as np
import socket
import pickle
import random

#Function to transmit data over TCP/IP
def transmit_data_over_tcpip(data):
    TCP_IP = '10.136.196.128' 
    TCP_PORT = 9999  #Port number selected

    #Creates a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((TCP_IP, TCP_PORT))
    server_socket.listen(1)

    print("Waiting for connection...")
    conn, addr = server_socket.accept()
    print('Connection address:', addr)

    #Serialises and sends data
    data_bytes = pickle.dumps(data)
    conn.send(data_bytes)
    print("Data transmitted successfully.")

    #Closes the connection
    conn.close()


def analyse_EMG_signal(signal, sampling_rate, threshold, ethanSignal, alexSignal):
    #Set Parameters
    GAIN = 1.0
    SAMPLING_RATE = sampling_rate
    THRESHOLD = threshold
    WINDOW_SIZE = 5

    #Apply bandpass filter
    filteredEMG = signal  #Placeholder, not actually filtering

    #Offset signal
    amplitude_offset, filteredEMG_offset, rectified_signal = offset_signal(signal, filteredEMG, THRESHOLD)

    #Calculate metrics
    mav_values, zcr_values, wl_values, window_times, envelope, rms_values = calculate_window_metrics(rectified_signal, filteredEMG_offset, SAMPLING_RATE, THRESHOLD, WINDOW_SIZE)
    frequencies, P1 = compute_spectrum(signal, SAMPLING_RATE)
    anotherFrequencies, PSD = compute_psd(signal, SAMPLING_RATE)
    #Display full window metrics
    rms_amplitude_full_window = np.sqrt(np.mean(rectified_signal ** 2))
    print('Full Window RMS Amplitude:', rms_amplitude_full_window)

    mav_value_full_window = np.mean(np.abs(rectified_signal))
    print('Full Window Mean Absolute Value (MAV):', mav_value_full_window)

    zcr_full_window = np.sum((filteredEMG_offset[:-1] < THRESHOLD) & (filteredEMG_offset[1:] >= THRESHOLD))
    print('Full Window Zero Crossing Rate (ZCR):', zcr_full_window)

        #Return the analysis results
    return {
        'rms_values': rms_values,
        'mav_values': mav_values,
        'zcr_values': zcr_values,
        'wl_values': wl_values,
        'window_times': window_times,
        'envelope': envelope,
        'rectified_signal': rectified_signal,
        'signal': signal,
        'rms_amplitude_full_window': rms_amplitude_full_window,
        'mav_value_full_window': mav_value_full_window,
        'zcr_full_window': zcr_full_window,
        'frequencies': frequencies,
        'P1': P1,
        'PSD': PSD,
        'IMU_signal': ethanSignal,
        'FSR_signal': alexSignal
        
    }


def bandpass_filter(signal, cutoff_freqs, sampling_rate):
    #Placeholder for demonstration
    return signal


def offset_signal(signal, filteredEMG, THRESHOLD):
    #Placeholder for demonstration
    return signal, filteredEMG, np.abs(filteredEMG)

def calculate_window_metrics(rectified_signal, filteredEMG_offset, sampling_rate, THRESHOLD, windowSize):
    num_windows = len(rectified_signal) // windowSize
    print("num_windows:", num_windows)
    print("length of rect signal:", len(rectified_signal)) 
    print("windowSize:", windowSize) 
    window_times = np.zeros(num_windows)

    envelope = np.ones_like(window_times)  #Initialise envelope with ones, matching the length of window_times
    rms_values = np.ones(num_windows)
    mav_values = np.ones(num_windows)
    zcr_values = np.ones(num_windows)
    wl_values = np.ones(num_windows)

    for i in range(num_windows):
        start_index = i * windowSize
        end_index = min((i + 1) * windowSize, len(rectified_signal))
        window_data = rectified_signal[start_index:end_index]
        window_data_f = filteredEMG_offset[start_index:end_index]
        print("window data: ", window_data) 

        zcr_values[i] = np.sum((window_data_f[:-1] < THRESHOLD) & (window_data_f[1:] >= THRESHOLD))
        wl_values[i] = np.sum(np.abs(np.diff(window_data)))
        print("wl value:", wl_values[i])
        mav_values[i] = np.mean(np.abs(window_data))
        rms_values[i] = np.sqrt(np.mean(window_data ** 2))

        #Calculates the midpoint of the window for window_times
        window_times[i] = start_index / sampling_rate + (end_index - start_index) / (2 * sampling_rate)

        #Assign RMS value to the corresponding window in the envelope
        envelope[i] = rms_values[i]

    envelope = np.convolve(envelope, np.ones(int(0.5 * sampling_rate)) / (int(0.5 * sampling_rate)), mode='same')
    print("mav_values:", mav_values)
    print("zcr_values:", zcr_values)
    print("wl_values:", wl_values)
    print("window_times:", window_times)
    print("envelope:", envelope)
    print("rms_values:", rms_values)
    return mav_values, zcr_values, wl_values, window_times, envelope, rms_values

def compute_spectrum(signal, sampling_rate):
    #Computes the FFT of the signal
    fft_signal = np.fft.fft(signal)

    #Computes the one-sided spectrum
    N = len(signal)  #Length of the signal
    P2 = np.abs(fft_signal / N)  #Two-sided spectrum
    P1 = P2[:N//2+1]  #One-sided spectrum
    P1[1:-1] = 2 * P1[1:-1]  #Adjusts the amplitude of the spectrum

    #Computes the frequency vector
    frequencies = np.arange(N // 2 + 1) * sampling_rate / N
    print("frequencies:", frequencies)
    print("P1:", P1)

    return frequencies, P1

def compute_psd(signal, sampling_rate):
    #Computes the FFT of the signal
    fft_signal = np.fft.fft(signal)

    #Computes the one-sided spectrum
    N = len(signal)  #Length of the signal
    P2 = np.abs(fft_signal / N)  #Two-sided spectrum
    P1 = P2[:N//2+1]  #One-sided spectrum
    P1[1:-1] = 2 * P1[1:-1]  #Adjusts the amplitude of the spectrum

    #Computes the frequency vector
    frequencies = np.arange(N // 2 + 1) * sampling_rate / N

    #Computes the power spectral density (PSD)
    psd = P1 ** 2 / (sampling_rate / N)  #Power spectral density (PSD)
    print("PSD:", psd)
    print("frequencies:", frequencies)

    return frequencies, psd



def plot_results(window_times, rectified_signal, envelope, rms_values, mav_values, zcr_values, wl_values, sampling_rate):
    plt.figure(figsize=(10, 6))
    plt.subplot(4, 1, 1)
    plt.plot(rectified_signal, label='Rectified EMG Signal')
    plt.plot(envelope, label='Envelope EMG Signal')
    plt.xlabel('Time')
    plt.ylabel('Amplitude')
    plt.title('Rectified and Envelope EMG Signals')
    plt.legend()
    plt.grid(True)

    plt.subplot(4, 1, 2)
    plt.plot(window_times, rms_values, label='RMS Amplitude')
    plt.plot(window_times, mav_values, label='MAV')
    plt.xlabel('Time (s)')
    plt.ylabel('Magnitude')
    plt.title('RMS Amplitude and MAV')
    plt.legend()
    plt.grid(True)

    plt.subplot(4, 1, 3)
    plt.plot(window_times, zcr_values, label='Zero Crossing Rate')
    plt.plot(window_times, wl_values, label='Waveform Length')
    plt.xlabel('Time (s)')
    plt.ylabel('Magnitude')
    plt.title('Zero Crossing Rate and Waveform Length')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


#Configure GPIO
BUTTON_PIN = 26
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Function to execute code when external button pressed
def execute_code(channel):
    print("Button pressed! Executing code...")
    
    #Bluetooth setup
    if not os.path.exists('/dev/rfcomm1'):
        os.system('sudo rfcomm bind 1 98:D3:B1:FE:66:C1')
        time.sleep(1)

    bluetoothSerial = serial.Serial("/dev/rfcomm1", baudrate=9600)
    time.sleep(1)
    #ADD BluetoothSerialEthan and bluetoothSerialAlex line here

    #Data collection
    ethan_data = []
    alex_data = []
    received_data = []
    time_values = []
    start_time = time.time()

    while True:
        RXData = bluetoothSerial.readline().strip().decode("utf-8")
        eData = random.randint(0, 1023) #generate random integer between 0 and 1023 (ADC sclaed values)
        aData = random.randint(0, 1023)
        #swap above for bluetoothSerialEthan and bluetoothSerialAlex
        
        print("Received data from Arduino:", RXData)

        received_data.append(float(RXData))
        ethan_data.append(float(eData))
        alex_data.append(float(aData)) 
        current_time = time.time()
        elapsed_time = current_time - start_time

        time_values.append(elapsed_time)

        if elapsed_time >= 15:
            print("Received data array:", received_data)
            print("Received Ethan array:", ethan_data)
            print("Received Alex array:", alex_data)
            plt.grid(True)
            plt.show()
            #Analyses the EMG signal
            analysis_results = analyse_EMG_signal(np.array(received_data), sampling_rate=1000, threshold=500, ethanSignal=np.array(ethan_data), alexSignal=np.array(alex_data))
            #Add ethans and Alex's calculations into my analysis_results function
            #Transmits the analysis results over TCP/IP
            transmit_data_over_tcpip(analysis_results)
            break

#Event listener for button press
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=execute_code, bouncetime=300)

try:
    print("Waiting for button press...")
    while True:
        time.sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()