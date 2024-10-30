import time
import Adafruit_ADS1x15
import board
import busio
import adafruit_ds3231
import datetime as dt
from multiprocessing import Queue

def get_rtc_time(ds3231):
    """
    Retrieve current time from the DS3231 RTC module.
    Returns a formatted string for timestamp including milliseconds.
    """
    now = ds3231.datetime
    milliseconds = int((time.perf_counter() % 1) * 1000)
    now_dt = dt.datetime(now.tm_year, now.tm_mon, now.tm_mday,
                         now.tm_hour, now.tm_min, now.tm_sec, milliseconds * 1000)
    return now_dt.strftime('%H:%M:%S.%f')[:-3]

def log_data(queue):

    i2c = busio.I2C(board.SCL, board.SDA)
    ds3231 = adafruit_ds3231.DS3231(i2c)


    adc = Adafruit_ADS1x15.ADS1115()
    GAIN = 1
    DATA_RATE = 250


    adc.start_adc_difference(0, gain=GAIN, data_rate=DATA_RATE)

    try:
        while True:

            differential_value = adc.get_last_result()


            timestamp = get_rtc_time(ds3231)


            queue.put(differential_value)

            time.sleep(0.0038)  

    except KeyboardInterrupt:
        adc.stop_adc()
        print("ADC sampling stopped.")


def start_logger(queue):
    log_data(queue)
