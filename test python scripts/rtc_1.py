import time
import csv
import os
from datetime import datetime
import Adafruit_ADS1x15
import board
import busio
import adafruit_ds3231
import datetime as dt

def get_rtc_time(ds3231):
    """
    Retrieve current time from the DS3231 RTC module.
    Returns a formatted string for timestamp including milliseconds.
    """
    now = ds3231.datetime  # Get time as a struct_time
    
    # Calculate milliseconds using system's time
    milliseconds = int((time.perf_counter() % 1) * 1000)  # Get milliseconds part

    # Convert struct_time to datetime
    now_dt = dt.datetime(now.tm_year, now.tm_mon, now.tm_mday, 
                         now.tm_hour, now.tm_min, now.tm_sec, milliseconds * 1000)

    return now_dt.strftime('%H:%M:%S.%f')[:-3]  # Format to HH:MM:SS.mmm

def log_data_to_csv(file_path):
    # Initialize I2C for RTC
    i2c = busio.I2C(board.SCL, board.SDA)
    ds3231 = adafruit_ds3231.DS3231(i2c)

    # Initialize ADC
    adc = Adafruit_ADS1x15.ADS1115()
    GAIN = 1
    DATA_RATE = 250

    # Start ADC in differential mode
    adc.start_adc_difference(0, gain=GAIN, data_rate=DATA_RATE)

    # Create CSV file
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
                next_time = time.perf_counter()
                # Fetch differential value from ADC
                differential_value = adc.get_last_result()

                # Get timestamp from DS3231 RTC
                timestamp = get_rtc_time(ds3231)

                # Store data in buffer
                buffer.append([timestamp, differential_value])
                

                # Write buffer to CSV if full
                if len(buffer) >= buffer_size:
                    csv_writer.writerows(buffer)
                    buffer = []
                    print(f'Message appended successfully')

                next_time += 0.0038
                sleep_time = next_time - time.perf_counter()
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            # Stop ADC and save remaining buffer
            adc.stop_adc()
            if buffer:
                csv_writer.writerows(buffer)
            print("Logging stopped. Data saved to:", csv_file_path)

# Define path for CSV storage
file_path = '/home/ERIC/Desktop/fyp/Logger_data'

log_data_to_csv(file_path)
