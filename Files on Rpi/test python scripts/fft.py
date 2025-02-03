import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import numpy as np
import Adafruit_ADS1x15


adc = Adafruit_ADS1x15.ADS1115(address=0x48, busnum=1)


GAIN = 1


sampling_rate = 250  


sampling_period = 1.0 / sampling_rate


x_len = 500


y_range = [-65000, 65000]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
xs = list(range(0, x_len))
ys = [0] * x_len
ax1.set_ylim(y_range)
ax2.set_xlim(0, sampling_rate // 2)
ax2.set_ylim(0, 4000)

line1, = ax1.plot(xs, ys)
line2, = ax2.plot(xs, ys)


ax1.set_title('Geophone Data')
ax1.set_xlabel('Data Points (Approximately 250 Readings each Second)')
ax1.set_ylabel('Voltage Value Post Gain Adjustment')
ax2.set_title('Fourier Transform')
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('Amplitude')

def animate(i, ys):

    loop_start_time = time.time()

    value = adc.read_adc_difference(0, gain=GAIN)

    ys.append(value)

    ys = ys[-x_len:]

    line1.set_ydata(ys)

    # Perform Fourier transform
    yf = np.fft.fft(ys)
    xf = np.fft.fftfreq(len(ys), sampling_period)[:len(ys)//2]
    line2.set_xdata(xf)
    line2.set_ydata(2.0/x_len * np.abs(yf[:len(ys)//2]))

    loop_end_time = time.time()
    loop_duration = loop_end_time - loop_start_time

    sleep_time = sampling_period - loop_duration
    if sleep_time > 0:
        time.sleep(sleep_time)

    return line1, line2

ani = animation.FuncAnimation(fig, animate, fargs=(ys,), interval=1, blit=True)
plt.tight_layout()
plt.show()
