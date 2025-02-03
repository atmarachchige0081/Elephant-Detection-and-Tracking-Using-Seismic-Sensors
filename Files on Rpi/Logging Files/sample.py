import smbus2
import RPi.GPIO as GPIO
import time
import csv
import multiprocessing
from datetime import datetime

bus = smbus2.SMBus(1)
DS3231_ADDRESS = 0x68
DS3231_CONTROL_REG = 0x0E

interrupt_pin = 17
interrupt_triggered = False
sample_buffer = multiprocessing.Queue()   


def setup_ds3231():
    control_byte = bus.read_byte_data(DS3231_ADDRESS, DS3231_CONTROL_REG)
    control_byte &= ~0x04 
    control_byte |= 0x00   
    bus.write_byte_data(DS3231_ADDRESS, DS3231_CONTROL_REG, control_byte)


def interrupt_handler(channel):
    global interrupt_triggered
    interrupt_triggered = True


def csv_writer_process(buffer):
    with open('samples_log.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp'])  
        
        while True:
            if not buffer.empty():
                data = buffer.get()
                if data == "STOP":
                    break
                writer.writerow([data])  
            time.sleep(0.01)  

def get_rtc_time():
    seconds = bus.read_byte_data(DS3231_ADDRESS, 0x00)  
    minutes = bus.read_byte_data(DS3231_ADDRESS, 0x01) 
    hours = bus.read_byte_data(DS3231_ADDRESS, 0x02)  
    
   
    return f"{hours:02x}:{minutes:02x}:{seconds:02x}"


def log_sample(buffer, base_time, ms_increment):
    
    timestamp = base_time + f".{ms_increment:03d}"
    buffer.put(timestamp)

GPIO.setmode(GPIO.BCM)
GPIO.setup(interrupt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(interrupt_pin, GPIO.FALLING, callback=interrupt_handler, bouncetime=200)

setup_ds3231()

csv_process = multiprocessing.Process(target=csv_writer_process, args=(sample_buffer,))
csv_process.start()

try:
    while True:
        if interrupt_triggered:
            interrupt_triggered = False
            

            base_time = get_rtc_time()
            print(f"Interrupt! Time: {base_time}")
            

            for sample_count in range(250):
                
                ms_increment = sample_count * 4
                
                log_sample(sample_buffer, base_time, ms_increment)
                
                time.sleep(0.004)

except KeyboardInterrupt:
    sample_buffer.put("STOP")
    csv_process.join()  
    GPIO.cleanup()
