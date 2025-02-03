import numpy as np
from scipy import signal
from scipy.fftpack import fft
import tflite_runtime.interpreter as tflite
from multiprocessing import Queue, Process
import logger 

sampling_rate = 250
nyquist = 0.5 * sampling_rate
cutoff_freq = 100  
window_size = 100


interpreter = tflite.Interpreter(model_path="time_domain_model.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()


def butter_lowpass(cutoff, nyquist, order=4):
    normal_cutoff = cutoff / nyquist
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def apply_lowpass_filter(data, cutoff, sampling_rate, order=4):
    nyquist = 0.5 * sampling_rate
    b, a = butter_lowpass(cutoff, nyquist, order=order)
    filtered_data = signal.lfilter(b, a, data)
    return filtered_data


def apply_gain(data, gain):
    return data * gain


def apply_fft(signal):
    fft_values = np.abs(fft(signal))
    freqs = np.fft.fftfreq(len(fft_values), 1/sampling_rate)
    return freqs[:len(fft_values)//2], fft_values[:len(fft_values)//2]

def zero_crossing_rate(signal):
    zero_crossings = np.where(np.diff(np.signbit(signal)))[0]
    return len(zero_crossings) / len(signal)

def extract_fourier_features(signal):
   
    freqs, fft_values = apply_fft(signal)

    
    peak_freq = freqs[np.argmax(fft_values)]

  
    spectral_spread = np.sqrt(np.sum(((freqs - peak_freq) ** 2) * fft_values) / np.sum(fft_values))

   
    rms_energy = np.sqrt(np.mean(np.square(signal)))

   
    zcr = zero_crossing_rate(signal)

    return [peak_freq, spectral_spread, rms_energy, zcr]


def classify(features):
    input_data = np.array(features, dtype=np.float32).reshape(1, -1)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    prediction = output_data[0][0]
    return prediction

def process_data(queue):
    buffer = []
    window_count = 1  
    while True:

        differential_value = queue.get()

        
        buffer.append(differential_value)


        if len(buffer) >= window_size:
            
            window = buffer[:window_size]

           
            filtered_signal_1 = apply_lowpass_filter(window, cutoff_freq, sampling_rate)
            filtered_signal_1 = apply_gain(filtered_signal_1, 2)

            
            amplified_signal = apply_gain(filtered_signal_1, 23)

           
            final_filtered_signal = apply_lowpass_filter(amplified_signal, cutoff_freq, sampling_rate)

            
            features = extract_fourier_features(final_filtered_signal)

            
            prediction = classify(features)
            if prediction > 0.5:
                print(f"Elephant detected in window {window_count} with confidence {prediction:.2f}")
            else:
                print(f"No elephant detected in window {window_count}, confidence {prediction:.2f}")

           
            window_count += 1

            
            buffer = buffer[window_size:]

if __name__ == "__main__":
    
    queue = Queue()

   
    logger_process = Process(target=logger.start_logger, args=(queue,))
    logger_process.start()

   
    process_data(queue)
