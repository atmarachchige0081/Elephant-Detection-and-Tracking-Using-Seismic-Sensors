import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import Adafruit_ADS1x15


adc = Adafruit_ADS1x15.ADS1115(address=0x48, busnum=1)


GAIN = 16


sampling_rate = 250  


sampling_period = 1.0 / sampling_rate


x_len = 500


y_range = [-60000, 60000]


fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
xs = list(range(0, x_len))
ys = [0] * x_len
ax.set_ylim(y_range)


line, = ax.plot(xs, ys)


plt.title('Geophone Data')
plt.xlabel('Data Points (Approximately 250 Readings each Second)')
plt.ylabel('Voltage Value Post Gain Adjustment')

def animate(i, ys):

    loop_start_time = time.time()

    value = adc.read_adc_difference(0, gain=GAIN)


    ys.append(value)

    ys = ys[-x_len:]

    line.set_ydata(ys)


    loop_end_time = time.time()
    loop_duration = loop_end_time - loop_start_time

    sleep_time = sampling_period - loop_duration
    if sleep_time > 0:
        time.sleep(sleep_time)

    return line,

ani = animation.FuncAnimation(fig, animate, fargs=(ys,), interval=1, blit=True, cache_frame_data = False)
plt.show()
