import json
import random
import time
import os
from datetime import datetime
import numpy as np
from flask import Flask, Response, render_template, flash, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
import sys
from phue import Bridge
import logging
import pygame
import pygame.camera

logging.basicConfig()
application = Flask(__name__)
random.seed()  # Initialize the random number generator

# Configuration
SECRET_KEY = os.urandom(32)
application.config['SECRET_KEY'] = SECRET_KEY
#sensor = '/sys/bus/w1/devices/28-01144fc1f1aa/w1_slave'
sensor1 = '/sys/bus/w1/devices/28-01144fedbdaa/w1_slave'
sensor2 = '/sys/bus/w1/devices/28-0114506580aa/w1_slave'
sensor3 = '/sys/bus/w1/devices/28-01145094fcaa/w1_slave'

data_file = 'data/temperature_data.csv'
threshold_file = 'data/tempthreshold.txt'
bridge_ip = '192.168.1.65'
# id for smart plug 
smart_plug_id = 5
# update frequency for chart in seconds
update_frequency = 5

try:
    pygame.camera.init()
    cam = pygame.camera.Camera("/dev/video0",(640,480))
    cam.start()
    webcam=True
except:
    print("webcam not working")
    webcam=False


def turn_plug(bool_on_off):
    # This function will set the plug either on or off, depending on input arg
    # Function returns status of plug (True for plug is on, False for plug is off)
    b.set_light(smart_plug_id, 'on', bool_on_off)
    light_on = b.get_light(smart_plug_id, 'on')
    return light_on

# try to connect to smart plug system
try:
    b = Bridge(bridge_ip)
    temp_control = True
except:
    print("Could not connect to Bridge")
    print("Automatic temperature control will not work")
    temp_control = False
# If the app is not registered and the button is not pressed, press the button and call connect() (this only needs to be run a single$
#b.connect()

if temp_control:
    # print initial status of plug
    print('light on is:' + str(turn_plug(True)))

class Threshold_Form(FlaskForm):
    temperature = StringField('Temperature', validators=[DataRequired()])
    submit = SubmitField('Save')

def gen(camera):
    while True:
        frame = cam.get_image()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@application.route('/', methods=['GET', 'POST'])
def index():
    # read temperature threshold file
    with open(threshold_file,'r') as f:
        forward_message = f.read()
    form = Threshold_Form()
    if form.validate_on_submit():
        flash('Temperature {}'.format(
            form.temperature.data))
        with open(threshold_file, "w") as tfile:
            tfile.write(form.temperature.data)
        return render_template('index.html',form=form,
                           forward_message=form.temperature.data) 
    return render_template('index.html',form=form,
                           forward_message=forward_message) 

@application.route('/deletealldata')
def deletealldata():
    # This endpoint will delete temperature file
    os.remove(data_file)
    return "file deleted"

@application.route('/chart-data')
def chart_data():
    # This function returns input data for chart, base on javascript snippet in index.html page
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
            if temp_control:
                if curr_temp<threshold_temp:
                   turn_plug(True)
                else: 
                   turn_plug(False)
            yield f"data:{json_data}\n\n"
            time.sleep(update_frequency)
    return_values = Response(get_temperature_data(), mimetype='text/event-stream')
    return return_values

@application.route('/video_feed')
def video_feed():
    return Response(gen(video_stream),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    application.run(host='0.0.0.0',port=80, debug=True, threaded=True)
