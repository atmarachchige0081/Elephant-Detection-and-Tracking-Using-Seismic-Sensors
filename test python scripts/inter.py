import smbus2
import RPi.GPIO as GPIO
import time

bus = smbus2.SMBus(1) 

DS3231_ADDRESS = 0x68


DS3231_CONTROL_REG = 0x0E


interrupt_pin = 17  


interrupt_triggered = False

# Function to setup DS3231 for 1Hz square wave output
def setup_ds3231():
    control_byte = bus.read_byte_data(DS3231_ADDRESS, DS3231_CONTROL_REG)
    control_byte &= ~0x04  # Clear INTCN to enable square wave output
    control_byte |= 0x00   # Set RS1 and RS2 to 0 (1Hz output)
    bus.write_byte_data(DS3231_ADDRESS, DS3231_CONTROL_REG, control_byte)

# Interrupt handler function
def interrupt_handler(channel):
    global interrupt_triggered
    interrupt_triggered = True

# Setup GPIO for the interrupt
GPIO.setmode(GPIO.BCM)
GPIO.setup(interrupt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# Add event detection with debounce time to avoid multiple triggers
GPIO.add_event_detect(interrupt_pin, GPIO.FALLING, callback=interrupt_handler, bouncetime=200)

# Initialize DS3231 for 1Hz square wave output
setup_ds3231()

try:
    while True:
        if interrupt_triggered:
            interrupt_triggered = False
            # Read the current time from DS3231
            seconds = bus.read_byte_data(DS3231_ADDRESS, 0x00)  # Read seconds register
            minutes = bus.read_byte_data(DS3231_ADDRESS, 0x01)  # Read minutes register
            hours = bus.read_byte_data(DS3231_ADDRESS, 0x02)    # Read hours register
            print(f"Interrupt! Time: {hours:02x}:{minutes:02x}:{seconds:02x}")
        
        time.sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()
