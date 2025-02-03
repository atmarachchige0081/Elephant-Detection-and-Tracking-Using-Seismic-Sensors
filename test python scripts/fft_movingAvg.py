import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import numpy as np
import Adafruit_ADS1x15

# Initialize the ADC
adc = Adafruit_ADS1x15.ADS1115(address=0x48, busnum=1)

# Gain setting for the ADC
GAIN = 16

# Desired sampling rate (samples per second)
sampling_rate = 250

# Calculate the sampling period
sampling_period = 1.0 / sampling_rate

# Number of data points to display on the plot
x_len = 500

# Range for the y-axis (adjust according to your application)
y_range = [-750, 750]

# Create figure for plotting with two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
xs = list(range(0, x_len))
ys = [0] * x_len
ax1.set_ylim(y_range)
ax2.set_xlim(0, sampling_rate // 2)
ax2.set_ylim(0, 50)

# Create blank lines. We will update these lines in the animate function
line1, = ax1.plot(xs, ys)
line2, = ax2.plot(xs, ys)

# Labels for the plots
ax1.set_title('Geophone Data')
ax1.set_xlabel('Data Points (Approximately 250 Readings each Second)')
ax1.set_ylabel('Voltage Value Post Gain Adjustment')
ax2.set_title('Fourier Transform')
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('Amplitude')

def moving_average(data, window_size):
    """Apply a moving average filter to the data."""
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

def animate(i, ys):
    try:
        loop_start_time = time.time()

        # Read the ADC value
        value = adc.read_adc_difference(0, gain=GAIN)

        # Add the new value to the list
        ys.append(value)

        # Limit the list to set number of elements
        ys = ys[-x_len:]

        # Apply the moving average filter
        window_size = 2  # Adjust the window size as needed
        if len(ys) >= window_size:
            filtered_ys = moving_average(ys, window_size)
            # Pad the filtered data to match the length of ys for consistent plotting
            filtered_ys = np.concatenate((np.zeros(window_size-1), filtered_ys))
        else:
            filtered_ys = ys

        # Update the line with filtered Y values
        line1.set_ydata(filtered_ys)

        # Perform Fourier transform on the filtered data
        yf = np.fft.fft(filtered_ys)
        xf = np.fft.fftfreq(len(filtered_ys), sampling_period)[:len(filtered_ys)//2]
        line2.set_xdata(xf)
        line2.set_ydata(2.0/x_len * np.abs(yf[:len(filtered_ys)//2]))

        # Calculate loop duration
        loop_end_time = time.time()
        loop_duration = loop_end_time - loop_start_time

        # Calculate sleep time to maintain the sampling rate
        sleep_time = sampling_period - loop_duration
        if sleep_time > 0:
            time.sleep(sleep_time)

    except Exception as e:
        print(f"Error: {e}")

    return line1, line2

# Set up plot to call animate function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(ys,), interval=1, blit=True)

# Adjust layout to prevent overlapping
plt.tight_layout()
plt.show()
