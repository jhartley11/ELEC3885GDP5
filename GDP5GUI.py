import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from functools import partial
import socket
import pickle
import numpy as np
import time

array_names = ["Signal", "Rectified Signal", "Envelope Signal", "Frequency Spectrum", "Power Spectral Density", "RMS Values", "MAV Values", "ZCR Values", "WL Values", "IMU Signal", "FSR Signal"]

def receive_data_over_tcpip():
    TCP_IP = '10.136.196.128'  #Raspberry Pi IP address
    TCP_PORT = 9999  #Port number listed in raspberry pi code

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((TCP_IP, TCP_PORT))

    data_bytes = b''
    while True:
        chunk = client_socket.recv(4096)  #Receive data in chunks of up to 4096 bytes

        if not chunk:
            break
        data_bytes += chunk

    analysis_results = pickle.loads(data_bytes)  #Deserialise the received byte string
    print("Received analysis results:", analysis_results)

    client_socket.close()

    return analysis_results

def extract_data(received_data):
    window_times = received_data['window_times']
    rectified_signal = received_data['rectified_signal']
    envelope = received_data['envelope']
    rms_values = received_data['rms_values']
    mav_values = received_data['mav_values']
    zcr_values = received_data['zcr_values']
    wl_values = received_data['wl_values']
    signal = received_data['signal']
    rms_amplitude_full_window = received_data['rms_amplitude_full_window']
    mav_value_full_window = received_data['mav_value_full_window']
    zcr_full_window = received_data['zcr_full_window']
    frequencies = received_data['frequencies']
    P1 = received_data['P1']
    PSD = received_data['PSD']
    IMU_signal = received_data['IMU_signal']
    FSR_signal = received_data['FSR_signal']

    #Interpolate rectified signal to match window_times - synchronisation
    signal_length = len(rectified_signal)
    signal_times = np.linspace(0, window_times[-1], signal_length)
    interpolated_rectified_signal = np.interp(window_times, signal_times, rectified_signal)
    interpolated_signal = np.interp(window_times, signal_times, signal)
    interpolated_IMU_signal = np.interp(window_times, signal_times, IMU_signal)
    interpolated_FSR_signal = np.interp(window_times, signal_times, FSR_signal)

    return (window_times, interpolated_rectified_signal, interpolated_signal, envelope, rms_values, mav_values, zcr_values, wl_values,
            rms_amplitude_full_window, mav_value_full_window, zcr_full_window, frequencies, P1, PSD, interpolated_IMU_signal, interpolated_FSR_signal)

def create_plot(ax, data_to_plot, labels, selected_arrays, array_names):
    ax.clear()
    for i, (data, label) in enumerate(zip(data_to_plot, labels)):
        if selected_arrays[i].get():
            ax.plot(data, label=array_names[i])  #Legend is array names listed
    ax.legend()
    ax.grid(True)
    ax.figure.canvas.draw()

#Creates main window
root = tk.Tk()
root.title("PlotSelector")

#Creates dictionary to hold selected arrays for each plot frame
selected_arrays_dict = {}

def add_plot():
    global data_arrays  #Access global data_arrays
    if len(plot_frames) >= 4:  #Max plots is 4
        return
    plot_frame = tk.Frame(root, bd=2, relief=tk.SOLID)
    plot_frame.grid(row=len(plot_frames)//2, column=len(plot_frames)%2, sticky="nsew", padx=10, pady=10)
    plot_frames.append(plot_frame)
    selected_arrays = [tk.BooleanVar(value=False) for _ in range(len(data_arrays))]
    selected_arrays_dict[plot_frame] = selected_arrays
    update_plots()
    if len(plot_frames) >= 4:
        add_button.config(state="disabled")

def remove_plot():
    if plot_frames:
        plot_frame = plot_frames.pop()
        plot_frame.destroy()
        del selected_arrays_dict[plot_frame]
        update_plots()
    if len(plot_frames) < 4:
        add_button.config(state="normal")

#Updates the plots based on user selection
def update_plots():
    global data_arrays, array_names, frequencies, P1, PSD, window_times  #Adds frequencies and P1 as global variables
    for plot_frame, selected_arrays in selected_arrays_dict.items():
        for widget in plot_frame.winfo_children():
            widget.destroy()
        fig = Figure(figsize=(4, 3), dpi=100)
        fig.subplots_adjust(bottom=0.2, left=0.2)
        ax = fig.add_subplot(111)
        checkboxes = []
        row = 0
        for i, (data, label) in enumerate(zip(data_arrays, array_names)):
            if data.any():
                var = selected_arrays[i]
                callback = partial(update_plot_with_selection, ax, data_arrays, selected_arrays, array_names, frequencies, P1, PSD, window_times)
                var.trace_add("write", callback)
                checkbox = ttk.Checkbutton(plot_frame, text=label, variable=var)
                checkbox.grid(row=row, column=0, sticky="w")
                checkboxes.append(checkbox)
                row += 1

        update_plot_with_selection(ax, data_arrays, selected_arrays, array_names, frequencies, P1, PSD, window_times)
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=1, rowspan=row, sticky="nsew")

def show_full_window_values():
    global full_window_data
    full_window = tk.Toplevel(root)
    full_window.title("Full Window Values")

    #Creates frames for each label
    frame_rms = tk.Frame(full_window)
    frame_mav = tk.Frame(full_window)
    frame_zcr = tk.Frame(full_window)

    #Packs each label within its respective frame
    tk.Label(frame_rms, text=f"Full Window RMS Amplitude = {full_window_data[0]}").pack(anchor="w")
    tk.Label(frame_mav, text=f"Full Window MAV = {full_window_data[1]}").pack(anchor="w")
    tk.Label(frame_zcr, text=f"Full Window ZCR = {full_window_data[2]}").pack(anchor="w")

    #Packs each frame
    frame_rms.pack(anchor="w")
    frame_mav.pack(anchor="w")
    frame_zcr.pack(anchor="w")

def update_plot_with_selection(ax, data_to_plot, selected_arrays, array_names, frequencies, P1, PSD, window_times, *_):
    ax.clear()

    freq_spectrum_selected = selected_arrays[array_names.index("Frequency Spectrum")].get()  #Checks if "Frequency Spectrum" checkbox is selected
    psd_selected = selected_arrays[array_names.index("Power Spectral Density")].get()  #Checks if "PSD" checkbox is selected

    #If "Frequency Spectrum" checkbox is selected, plot only the selected arrays
    if freq_spectrum_selected:
        for i, (data, label) in enumerate(zip(data_to_plot, array_names)):
            if selected_arrays[i].get() and label == "Frequency Spectrum":
                ax.plot(frequencies, P1, label="Frequency Spectrum")  #Plot frequencies vs P1
                ax.set_xlabel('Frequency (Hz)')
                ax.set_ylabel('Power (dB)')
    elif psd_selected:
        for i, (data, label) in enumerate(zip(data_to_plot, array_names)):
            if selected_arrays[i].get() and label == "Power Spectral Density":
                ax.plot(frequencies, PSD, label="Power Spectral Density")  #Plot frequencies vs PSD
                ax.set_xlabel('Frequency (Hz)')
                ax.set_ylabel('Power/Frequency (dB/Hz)')
    else:
        #If "Frequency Spectrum" checkbox is not selected, plot all selected arrays
        for i, (data, label) in enumerate(zip(data_to_plot, array_names)):
            if selected_arrays[i].get():
                if label in ["Envelope Signal", "RMS Values", "MAV Values", "ZCR Values", "WL Values", "Rectified Signal", "Signal", "IMU Signal", "FSR Signal"]:
                    ax.plot(window_times, data, label=label)  #Plot specific values with window times
                    ax.set_xlabel('Time (s)')
                    ax.set_ylabel(label)
                else:
                    ax.plot(data, label=label)
                    ax.set_xlabel('Time (s)')
                    ax.set_ylabel('Amplitude')

    ax.legend()
    ax.grid(True)
    ax.figure.canvas.draw()

#Buttons to add and remove plots
add_button = ttk.Button(root, text="+ Add Plot", command=add_plot)
add_button.grid(row=0, column=2, sticky="nsew")
remove_button = ttk.Button(root, text="- Remove Plot", command=remove_plot)
remove_button.grid(row=1, column=2, sticky="nsew")

plot_frames = []


# Button for displaying full window values
full_window_button = ttk.Button(root, text="Full Window Values", command=show_full_window_values, width=20)
full_window_button.grid(row=2, column=2, pady=5)


def start_plotting():
    global data_arrays, frequencies, P1, PSD, full_window_data, window_times  #Adds frequencies and P1 as global variables
    start_time = time.perf_counter()  #Start timer
    analysis_results = receive_data_over_tcpip()  #Calls function to receive data
    end_time = time.perf_counter()  #End timer
    latency = (end_time - start_time) * 1000  #Calculate latency in milliseconds
    print("Latency from button press to TCP/IP connection:", latency, "milliseconds")

    (window_times, rectified_signal, signal, envelope, rms_values, mav_values, zcr_values, wl_values,
     rms_amplitude_full_window, mav_value_full_window, zcr_full_window, frequencies, P1, PSD, IMU_signal,
     FSR_signal) = extract_data(analysis_results)
    data_arrays = [signal, rectified_signal, envelope, frequencies, PSD, rms_values, mav_values, zcr_values, wl_values,
                   IMU_signal, FSR_signal]
    full_window_data = [rms_amplitude_full_window, mav_value_full_window, zcr_full_window]
    update_plots()
    add_button.grid(row=0, column=2, sticky="nsew")
    remove_button.grid(row=1, column=2, sticky="nsew")
    full_window_button.grid(row=2, column=2, pady=5)
    start_button.grid_remove()  #Removes "Connect" button after it's pressed initially


#Creates "Connect" button
start_button = ttk.Button(root, text="Connect", command=start_plotting)
start_button.grid(row=3, column=2, sticky="nsew")

#Hides buttons for adding/removing plots and displaying full window values initially
add_button.grid_remove()
remove_button.grid_remove()
full_window_button.grid_remove()

root.mainloop()