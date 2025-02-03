import time
import csv
import os
import threading
from datetime import datetime
import Adafruit_ADS1x15
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

def log_data_to_csv(file_path, data_queue):
    adc = Adafruit_ADS1x15.ADS1115()
    GAIN = 16
    DATA_RATE = 860
    adc.start_adc_difference(0, gain=GAIN, data_rate=DATA_RATE)

    start_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file_name = f"{start_time}_geophone_data.csv"
    csv_file_path = os.path.join(file_path, csv_file_name)

    buffer = []
    buffer_size = 1000

    with open(csv_file_path, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Timestamp', 'Differential Value'])

        try:
            while True:
                differential_value = adc.get_last_result()
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                buffer.append([timestamp, differential_value])
                data_queue.append((timestamp, differential_value))

                if len(buffer) >= buffer_size:
                    csv_writer.writerows(buffer)
                    buffer = []

                print(f'{timestamp} - Differential Value (AIN0 - AIN1): {differential_value}')
                time.sleep(0.003)

        except KeyboardInterrupt:
            if buffer:
                csv_writer.writerows(buffer)
            adc.stop_adc()
            print("Logging stopped. Data saved to:", csv_file_path)

def live_plot(data_queue):
    fig, ax = plt.subplots()
    x_data = deque(maxlen=100)
    y_data = deque(maxlen=100)
    line, = ax.plot([], [])

    def init():
        ax.set_xlim(0, 100)
        ax.set_ylim(-1000, 1000)
        return line,

    def update_plot(frame):
        while data_queue:
            timestamp, value = data_queue.popleft()
            x_data.append(timestamp)
            y_data.append(value)

        line.set_data(range(len(y_data)), y_data)
        return line,

    ani = animation.FuncAnimation(fig, update_plot, init_func=init, interval=100, blit=True)
    plt.title('Geophone Data')
    plt.xlabel('Data Points (Approximately 250 Readings each Second)')
    plt.ylabel('Voltage Value Post Gain Adjustment')
    plt.show()

file_path = '/home/ERIC/Desktop/fyp'
data_queue = deque()

logging_thread = threading.Thread(target=log_data_to_csv, args=(file_path, data_queue))

logging_thread.start()
live_plot(data_queue)

logging_thread.join()
