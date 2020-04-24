import json
import random
import time
import os
from datetime import datetime
import numpy as np
from flask import Flask, Response, render_template, flash, redirect

import time
import sys
from phue import Bridge
import logging

application = Flask(__name__)
random.seed()  # Initialize the random number generator

#sensor = '/sys/bus/w1/devices/28-01144fc1f1aa/w1_slave'
sensor1 = '/sys/bus/w1/devices/28-01144fedbdaa/w1_slave'
sensor2 = '/sys/bus/w1/devices/28-0114506580aa/w1_slave'
sensor3 = '/sys/bus/w1/devices/28-01145094fcaa/w1_slave'

data_file = 'data/temperature_data.csv'
threshold_file = 'data/tempthreshold.txt'


logging.basicConfig()
b = Bridge('192.168.1.65')
# If the app is not registered and the button is not pressed, press the button and call connect() (this only needs to be run a single$
#b.connect()

def turn_light(bool_on_off):
    b.set_light(5, 'on', bool_on_off)
    light_on = b.get_light(5, 'on')
    return light_on

print('light on is:' + str(turn_light(True)))

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

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

import os
SECRET_KEY = os.urandom(32)
application.config['SECRET_KEY'] = SECRET_KEY

class LoginForm(FlaskForm):
    temperature = StringField('Temperature', validators=[DataRequired()])
    submit = SubmitField('Save')

@application.route('/', methods=['GET', 'POST'])
def index():
    # read temperature threshold file
    with open(threshold_file,'r') as f:
        forward_message = f.read()
    form = LoginForm()
    if form.validate_on_submit():
        flash('Temperature {}'.format(
            form.temperature.data))
        with open(threshold_file, "w") as tfile:
            tfile.write(form.temperature.data)
        return render_template('index.html',form=form,
                           forward_message=form.temperature.data) 
    return render_template('index.html',form=form,
                           forward_message=forward_message) 
#    return render_template('index.html')

@application.route('/deletealldata')
def deletealldata():
    os.remove(data_file)
    return "file deleted"


@application.route('/chart-data')
def chart_data():
    def get_temperature_data():
        while True:
            my_data = np.genfromtxt(data_file, delimiter=',', dtype='str')
            dates = my_data[:,0]
            sensor1 = my_data[:,1].astype(float)
            sensor2 = my_data[:,2].astype(float)
            sensor3 = my_data[:,3].astype(float)
            json_data = json.dumps(
                {'time': list(dates), 'sensor1': list(sensor1),
                 'sensor2': list(sensor2),'sensor3': list(sensor3)})
            curr_temp = sensor1[-1]
            with open(threshold_file,'r') as f:
                threshold_temp = float(f.read())
            if curr_temp<threshold_temp:
               turn_light(True)
            else: 
               turn_light(False)
            yield f"data:{json_data}\n\n"
            time.sleep(5)
    return_values = Response(get_temperature_data(), mimetype='text/event-stream')
    return return_values


if __name__ == '__main__':
    application.run(host='0.0.0.0',port=80, debug=True, threaded=True)
