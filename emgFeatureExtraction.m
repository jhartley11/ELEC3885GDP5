%Define the filenames and gain for each condition
file_healthy = "emg_healthy.txt";
GAIN = 1;

%Process EMG data for each condition, applying gain to amplitude
[timeHealthy, amplitudeHealthy] = process_EMG_data(file_healthy, GAIN);

%The sampling rate of the text file is 4KHz 
SAMPLING_RATE = 4000; 

%Apply bandpass filter to the signal
filteredEMG_healthy = apply_bandpass_filter(amplitudeHealthy, [20 498], SAMPLING_RATE);

%Process signals for healthy EMG
[amplitudeHealthy_offset, filteredEMG_healthy_offset, rectified_healthy] = offset_signal(amplitudeHealthy, filteredEMG_healthy);

%Define the time ranges
start_time = 0;       % Start time
end_time = 12.715;    % End time

%Find the indices corresponding to the time ranges
start_indexH = find(timeHealthy >= start_time, 1);
end_indexH = find(timeHealthy <= end_time, 1, 'last');

%Calculate RMS amplitude for the entire signal
rmsAmplitudeFullWindowHealthy = rms(rectified_healthy(start_indexH:end_indexH));
disp(['RMS Amplitude for the entire signal (Healthy Signal): ', num2str(rmsAmplitudeFullWindowHealthy)]);

%Calculate MAV for the entire signal
mavValueFullWindowHealthy = mean(abs(rectified_healthy(start_indexH:end_indexH)));
disp(['Mean Absolute Value (MAV) for the entire signal (Healthy Signal): ', num2str(mavValueFullWindowHealthy)]);

%Calculate ZCR for the entire signal within the specified time range
zcrFullWindowHealthy = sum(filteredEMG_healthy_offset(start_indexH:end_indexH-1) < 0 & filteredEMG_healthy_offset(start_indexH+1:end_indexH) >= 0);
disp(['Zero Crossing Rate (ZCR) for the entire signal (Healthy Signal): ', num2str(zcrFullWindowHealthy)]);

%Compute the FFT of the unfiltered signal
fft_emg_healthy = fft(amplitudeHealthy);

%Compute the FFT of the filtered signal
fft_filteredEMG_healthy = fft(filteredEMG_healthy);

%Compute frequency spectrum of the signal
[frequencySpectrum_healthy, psd_healthy] = compute_spectrum(filteredEMG_healthy, SAMPLING_RATE);

%Calculate sliding window metrics
[mavValuesHealthy, zcrValuesHealthy, wlValuesHealthy, windowTimesHealthy, envelopeHealthy, rmsValuesHealthy] = calculate_window_metrics(rectified_healthy, filteredEMG_healthy_offset, timeHealthy, SAMPLING_RATE);

%Smoothing the envelopes using a moving average filter
smoothedEnvelopeHealthy = movmean(envelopeHealthy, 0.5 * SAMPLING_RATE); % Use a 0.5 second moving average window

%-------------PLOTS------------------
%Plot of raw signals
figure(1);
plot(timeHealthy, amplitudeHealthy, 'b', 'LineWidth', 1.5); 
xlabel('Time (s)');
ylabel('Amplitude (mV)');
title('Raw EMG Signal (Healthy)');
xlim([0,12.715]);
grid on;

%Plot of rectified signals
figure(2);
plot(timeHealthy, rectified_healthy, 'b', 'LineWidth', 1.5); 
xlabel('Time (s)');
ylabel('Amplitude (mV)');
title('Rectified Signal (Healthy)');
xlim([0,12.715]);
grid on;

% Plot of RMS Envelope of Signals
figure(3);
plot(timeHealthy, smoothedEnvelopeHealthy, 'b', 'LineWidth', 1.5);
xlabel('Time (s)');
ylabel('Amplitude (mV)');
title('RMS Envelope (Healthy)');
xlim([0,12.715]);
grid on;

%Plot of RMS Amplitude over Time (Sliding Window)
figure (4);
plot(windowTimesHealthy, rmsValuesHealthy, 'b', 'LineWidth', 1.5);
xlabel('Time (s)');
ylabel('RMS Amplitude (mV)');
title('RMS Amplitude over Time (Sliding Window - Healthy)');
xlim([0,12.715]);
grid on;

% Plot of Mean Absolute Value (MAV) over Time (Sliding Window Analysis)
figure (5);
plot(windowTimesHealthy, mavValuesHealthy, 'b', 'LineWidth', 1.5);
xlabel('Time (s)');
ylabel('MAV (mV)');
title('Mean Absolute Value (MAV) over Time - Healthy');
xlim([0,12.715]);
grid on;

%Plot of Zero Crossing Rate (ZCR) over Time (Sliding Window Analysis)
figure(6);
plot(windowTimesHealthy, zcrValuesHealthy, 'b', 'LineWidth', 1.5);
xlabel('Time (s)');
ylabel('Zero Crossing Rate');
title('Zero Crossing Rate (ZCR) over Time - Healthy');
xlim([0,12.715]);
grid on;

%Plot of Waveform Length (WL) over Time (Sliding Window Analysis)
figure(7);
plot(windowTimesHealthy, wlValuesHealthy, 'b', 'LineWidth', 1.5);
xlabel('Time (s)');
ylabel('Waveform Length');
title('Waveform Length (WL) over Time - Healthy');
xlim([0,12.715]);
grid on;

%Plot of frequency spectrum and PSD
figure(8);
plot(frequencySpectrum_healthy, psd_healthy, 'b', 'LineWidth', 1.5);
xlabel('Frequency (Hz)');
ylabel('Power/Frequency (dB/Hz)');
title('Frequency Spectrum and Power Spectral Density (Healthy)');
xlim([0,500]);
grid on;

function [time, amplitude] = process_EMG_data(filename, gain)
    %Load the data
    data = load(filename);

    %Process the time and amplitude
    time = data(:, 1);
    amplitude = data(:, 2);
end

function filtered_signal = apply_bandpass_filter(signal, freq_range, sampling_rate)
    %Design a bandpass filter
    [b, a] = butter(2, freq_range / (sampling_rate / 2), 'bandpass');
    
    %Apply the filter to the signal
    filtered_signal = filtfilt(b, a, signal);
end

function [signal_offset, filtered_signal_offset, rectified_signal] = offset_signal(signal, filtered_signal)
    %Offset the signal by subtracting the mean
    signal_offset = signal - mean(signal);
    filtered_signal_offset = filtered_signal - mean(filtered_signal);
    
    %Rectify the signal
    rectified_signal = abs(filtered_signal_offset);
end

function [frequencySpectrum, psd] = compute_spectrum(signal, sampling_rate)
    %Compute the FFT of the signal
    L = length(signal);
    fft_signal = fft(signal);
    
    %Compute the two-sided spectrum
    P2 = abs(fft_signal / L);
    
    %Compute the single-sided spectrum
    P1 = P2(1:L/2+1);
    P1(2:end-1) = 2*P1(2:end-1);
    
    %Compute the frequency axis
    frequencySpectrum = sampling_rate * (0:(L/2)) / L;
    
    %Compute the power spectral density (PSD)
    psd = (1 / (sampling_rate * L)) * abs(fft_signal).^2;
    psd = psd(1:L/2+1);
    psd(2:end-1) = 2 * psd(2:end-1);
end

function [mavValues, zcrValues, wlValues, windowTimes, envelope, rmsValues] = calculate_window_metrics(rectified_signal, filtered_signal_offset, time, sampling_rate)
    %Set window length and step size
    windowLength = 0.2 * sampling_rate; % 0.2 seconds
    stepSize = 0.1 * sampling_rate; % 0.1 seconds
    
    %Calculate number of windows
    numWindows = floor((length(rectified_signal) - windowLength) / stepSize) + 1;
    
    %Initialise arrays to hold MAV, ZCR, and WL values
    mavValues = zeros(numWindows, 1);
    zcrValues = zeros(numWindows, 1);
    wlValues = zeros(numWindows, 1);
    rmsValues = zeros(numWindows, 1);
    
    %Calculate metrics for each window
    for i = 1:numWindows
        startIdx = (i-1) * stepSize + 1;
        endIdx = startIdx + windowLength - 1;
        window = rectified_signal(startIdx:endIdx);
        window_offset = filtered_signal_offset(startIdx:endIdx);
        
        mavValues(i) = mean(window);
        zcrValues(i) = sum(window_offset(1:end-1) < 0 & window_offset(2:end) >= 0);
        wlValues(i) = sum(abs(diff(window)));
        rmsValues(i) = rms(window);
    end
    
    %Calculate window times
    windowTimes = (0:numWindows-1) * stepSize / sampling_rate;
    
    %Calculate envelope
    envelope = abs(hilbert(rectified_signal));
end

