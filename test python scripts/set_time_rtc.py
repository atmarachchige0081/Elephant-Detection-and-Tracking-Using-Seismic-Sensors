from datetime import datetime
import time
import board
import busio
import adafruit_ds3231

# Initialize I2C for RTC
i2c = busio.I2C(board.SCL, board.SDA)
ds3231 = adafruit_ds3231.DS3231(i2c)

# Get current system time from Raspberry Pi
current_time = datetime.now()

# Convert datetime.datetime to time.struct_time
current_time_struct = current_time.timetuple()

# Set the DS3231 time
ds3231.datetime = current_time_struct

print("RTC time has been set to:", ds3231.datetime)
