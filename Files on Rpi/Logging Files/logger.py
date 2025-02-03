import smbus2
import RPi.GPIO as GPIO
import time
import csv
import multiprocessing
from datetime import datetime
import Adafruit_ADS1x15
import os

adc = Adafruit_ADS1x15.ADS1115()
GAIN = 16
DATA_RATE = 250

bus = smbus2.SMBus(1)
DS3231_ADDRESS = 0x68
DS3231_CONTROL_REG = 0x0E

interrupt_pin = 17
interrupt_triggered = False
sample_buffer = multiprocessing.Queue()


SAVE_PATH = "/home/ERIC/Desktop/Logging Files" 

def generate_filename():

    now = datetime.now()
    filename = now.strftime("%H:%M_%d-%m-%Y.csv")
    return os.path.join(SAVE_PATH, filename)

def setup_ds3231():
    control_byte = bus.read_byte_data(DS3231_ADDRESS, DS3231_CONTROL_REG)
    control_byte &= ~0x04  
    control_byte |= 0x00   
    bus.write_byte_data(DS3231_ADDRESS, DS3231_CONTROL_REG, control_byte)

def interrupt_handler(channel):
    global interrupt_triggered
    interrupt_triggered = True

def csv_writer_process(buffer, filename):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'ADC'])  
        
        while True:
            if not buffer.empty():
                data = buffer.get()
                if data == "STOP":
                    break
                writer.writerow(data) 
            time.sleep(0.01)  

def get_rtc_time():
    seconds = bus.read_byte_data(DS3231_ADDRESS, 0x00)  
    minutes = bus.read_byte_data(DS3231_ADDRESS, 0x01) 
    hours = bus.read_byte_data(DS3231_ADDRESS, 0x02)    

    return f"{hours:02x}:{minutes:02x}:{seconds:02x}"

def read_adc_value():
    return adc.get_last_result()  

def log_sample(buffer, base_time, ms_increment, adc_value):
    timestamp = base_time + f".{ms_increment:03d}"
    buffer.put([timestamp, adc_value])
    
    # Print the timestamp and ADC value in the terminal
    print(f"Timestamp: {timestamp}, ADC Result: {adc_value}")

GPIO.setmode(GPIO.BCM)
GPIO.setup(interrupt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(interrupt_pin, GPIO.FALLING, callback=interrupt_handler, bouncetime=200)

setup_ds3231()

csv_filename = generate_filename()
csv_process = multiprocessing.Process(target=csv_writer_process, args=(sample_buffer, csv_filename))
csv_process.start()

adc.start_adc_difference(0, gain=GAIN, data_rate=DATA_RATE)

try:
    while True:
        if interrupt_triggered:
            interrupt_triggered = False
            
            base_time = get_rtc_time()

            for sample_count in range(250):
                ms_increment = sample_count * 4
                adc_value = read_adc_value()
                log_sample(sample_buffer, base_time, ms_increment, adc_value)
                time.sleep(0.004)

except KeyboardInterrupt:
    sample_buffer.put("STOP")
    csv_process.join()  
    adc.stop_adc()  
    GPIO.cleanup()
