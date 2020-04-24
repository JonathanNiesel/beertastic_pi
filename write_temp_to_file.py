import time
import numpy as np
from datetime import datetime
import sys
import os

sensor1 = '/sys/bus/w1/devices/28-01144fedbdaa/w1_slave'
sensor2 = '/sys/bus/w1/devices/28-0114506580aa/w1_slave'
sensor3 = '/sys/bus/w1/devices/28-01145094fcaa/w1_slave'

data_file = 'data/temperature_data.csv'

def readTempSensor(sensorName) :
    """Aus dem Systembus lese ich die Temperatur der DS18B20 aus."""
    f = open(sensorName, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def readTempLines(sensorName) :
    lines = readTempSensor(sensorName)
    # Solange nicht die Daten gelesen werden konnten, bin ich hier in einer Endlosschleife
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = readTempSensor(sensorName)
    temperaturStr = lines[1].find('t=')
    # Ich überprüfe ob die Temperatur gefunden wurde.
    if temperaturStr != -1 :
        tempData = lines[1][temperaturStr+2:]
        tempCelsius = float(tempData) / 1000.0
        return tempCelsius

def write_temp():
    while True:
        temperature_data = np.array([datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                     readTempLines(sensor1),
                                     readTempLines(sensor2),
                                     readTempLines(sensor3)])
        with open(data_file, 'ab') as abc:
            np.savetxt(abc, [temperature_data], delimiter=",", fmt="%s") 
        time.sleep(3)

if __name__ == '__main__':
    write_temp()

