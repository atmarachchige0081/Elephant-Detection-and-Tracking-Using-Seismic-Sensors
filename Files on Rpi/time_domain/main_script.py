import numpy as np
from scipy import signal
import tflite_runtime.interpreter as tflite
from multiprocessing import Queue, Process
import logger  

sampling_rate = 250
nyquist = 0.5 * sampling_rate
cutoff_freq = 100
window_size = 100


interpreter = tflite.Interpreter(model_path= "time_model.tflite")
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

def rms_energy(window):
    return np.sqrt(np.mean(np.square(window)))

def zero_crossing_rate(window):
    zero_crossings = np.where(np.diff(np.signbit(window)))[0]
    return len(zero_crossings) / len(window)

def peak_to_peak_amplitude(window):
    return np.ptp(window)

def variance(window):
    return np.var(window)

def extract_time_series_features(window):
    rms = rms_energy(window)
    zcr = zero_crossing_rate(window)
    p2p = peak_to_peak_amplitude(window)
    var = variance(window)
    return [rms, zcr, p2p, var]

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
            final_filtered_signal = apply_lowpass_filter(filtered_signal_1, cutoff_freq, sampling_rate)


            features = extract_time_series_features(final_filtered_signal)


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
