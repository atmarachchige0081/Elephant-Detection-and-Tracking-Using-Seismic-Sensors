import Adafruit_ADS1x15

adc = Adafruit_ADS1x15.ADS1115()

GAIN = 16
DATA_RATE = 250

adc.start_adc_difference(0, gain=GAIN, data_rate=DATA_RATE)

try:
    while True:
        differential_value = adc.get_last_result()
        
except KeyboardInterrupt:
    adc.stop_adc()
