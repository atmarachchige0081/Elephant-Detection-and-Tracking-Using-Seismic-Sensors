import time
import csv
import os
import threading
from datetime import datetime
import Adafruit_ADS1x15
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# Function to log data to CSV
def log_data_to_csv(file_path, data_queue):
    # Create an ADS1115 ADC (16-bit) instance
    adc = Adafruit_ADS1x15.ADS1115()

    # Define gain and data rate
    GAIN = 16
    DATA_RATE = 860  # 860 samples per second

    # Configure the ADS1115 for continuous differential mode
    adc.start_adc_difference(0, gain=GAIN, data_rate=DATA_RATE)

    # Get the start time for the CSV file name
    start_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file_name = f"{start_time}_geophone_data.csv"
    csv_file_path = os.path.join(file_path, csv_file_name)

    # Open the CSV file in write mode
    with open(csv_file_path, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        # Write the header row
        csv_writer.writerow(['Timestamp', 'Differential Value'])

        try:
            while True:
                # Read differential value in continuous mode
                differential_value = adc.get_last_result()

                # Get current timestamp
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                # Log data to CSV file
                csv_writer.writerow([timestamp, differential_value])

                # Add data to queue for plotting
                data_queue.append((timestamp, differential_value))

                # Print differential value with timestamp (optional)
                print(f'{timestamp} - Differential Value (AIN0 - AIN1): {differential_value}')

                # Sleep for a short time to mimic continuous reading
                time.sleep(0.0035)  # Adjust based on desired sampling rate

        except KeyboardInterrupt:
            # Stop continuous conversion mode
            adc.stop_adc()
            print("Logging stopped. Data saved to:", csv_file_path)

# Function to plot live data
def live_plot(data_queue):
    # Initialize plot
    fig, ax = plt.subplots()
    x_data = deque(maxlen=100)
    y_data = deque(maxlen=100)

    def update_plot(frame):
        while data_queue:
            timestamp, value = data_queue.popleft()
            x_data.append(timestamp)
            y_data.append(value)

        ax.clear()
        ax.plot(list(range(len(y_data))), y_data)
        ax.set_title('Live Geophone Data')
        ax.set_xlabel('Sample Number')
        ax.set_ylabel('Differential Value')

    ani = animation.FuncAnimation(fig, update_plot, interval=100)
    plt.show()

# Specify the path where the CSV file should be saved
file_path = '/home/ERIC/Desktop/fyp'  # Update this path accordingly

# Create a queue to share data between threads
data_queue = deque()

# Create threads for logging and plotting
logging_thread = threading.Thread(target=log_data_to_csv, args=(file_path, data_queue))
plotting_thread = threading.Thread(target=live_plot, args=(data_queue,))

# Start the threads
logging_thread.start()
plotting_thread.start()

# Wait for both threads to complete
logging_thread.join()
plotting_thread.join()
