import os
import csv
from datetime import datetime
import Adafruit_ADS1x15
from timeit import default_timer as timer

def log_data_to_csv(file_path):
    adc = Adafruit_ADS1x15.ADS1115()

    GAIN = 8
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
            last_time = timer()
            while True:
                current_time = timer()
                elapsed_time = current_time - last_time

                if elapsed_time >= 0.0038: 
                    differential_value = adc.get_last_result()
                    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                    buffer.append([timestamp, differential_value])
                    print(f'{timestamp} - Differential Value : {differential_value}')

                    if len(buffer) >= buffer_size:
                        csv_writer.writerows(buffer)
                        buffer = []

                    last_time = current_time

        except KeyboardInterrupt:
            adc.stop_adc()
            if buffer:
                csv_writer.writerows(buffer)
            print("Logging stopped. Data saved to:", csv_file_path)

file_path = '/home/ERIC/Desktop/fyp'  
log_data_to_csv(file_path)
