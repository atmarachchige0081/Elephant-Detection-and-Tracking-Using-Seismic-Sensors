import pandas as pd
import matplotlib.pyplot as plt

file_path = r'/home/ERIC/Desktop/fyp/20240708_104849_geophone_data.csv'
df = pd.read_csv(file_path)

print(df.columns)


print(df.head())


date_column = 'Timestamp'
value_column = 'Differential Value'

df[date_column] = pd.to_datetime(df[date_column], format='%H:%M:%S.%f')

df.set_index(date_column, inplace=True)


plt.figure(figsize=(10, 6))
plt.plot(df[value_column])
plt.title('Time Series Plot Human test using ESP32 Inbuilt ADC')
plt.xlabel('Timestamp')
plt.ylabel('Data')
plt.grid(True)
plt.show()
