import time
import board
import busio
import adafruit_ds3231
from datetime import datetime

def sync_rtc():
    # Initialize I2C bus for the Raspberry Pi
    i2c = busio.I2C(board.SCL, board.SDA)

    # Initialize RTC (address is typically 0x68 for DS3231)
    rtc = adafruit_ds3231.DS3231(i2c)

    # Get the current system time and convert to struct_time
    now = datetime.now().timetuple()

    # Set the RTC time to the current system time
    rtc.datetime = now

    print(f"RTC synced to {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    print("Disconnect this RTC and connect the next one.")

if __name__ == "__main__":
    sync_rtc()
