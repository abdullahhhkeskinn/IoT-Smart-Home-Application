import logging
import time
from flask import Flask, request, render_template
from flask_socketio import SocketIO, send, emit    
import gpiozero                                 
from gpiozero import  Device
from gpiozero.pins.pigpio import PiGPIOFactory
import dht11
import RPi.GPIO as GPIO

# Initialize Logging
logging.basicConfig(level=logging.WARNING)  # Global logging configuration
logger = logging.getLogger('main') 
logger.setLevel(logging.INFO) 

# initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

# Initialize GPIO
Device.pin_factory = PiGPIOFactory() #set gpiozero to use pigpio by default.

# Initilize Relays
relay1 = gpiozero.OutputDevice(20, active_high=True, initial_value=False)
relay2 = gpiozero.OutputDevice(21, active_high=True, initial_value=False)
dht_sensor = dht11.DHT11(pin = 26)

# Flask 
app = Flask(__name__) 
socketio = SocketIO(app)                         

"""
Flask & Flask-SocketIO Related Functions
"""
# @app.route apply to the raw Flask instance.
# Here we are serving a simple web page.
@app.route('/', methods=['GET'])
def index():
    return render_template('index_ws_client.html')                 

# Flask-SocketIO Callback Handlers
@socketio.on('connect')                                                              
def handle_connect():
    """Called when a remote web socket client connects to this server"""
    logger.info("Client {} connected.".format(request.sid)) 

    emit("relay1", relay1.value)                                                            
    emit("relay2", relay2.value)

# Send Feedback when a client disconnects
@socketio.on('disconnect')                                                           
def handle_disconnect():
    """Called with a client disconnects from this server"""
    logger.info("Client {} disconnected.".format(request.sid))

# LED1 Handler
@socketio.on('relay1')                                                                  
def handle_state(data):                                                              
    logger.info("Update to Relay 1 from client {}: {} ".format(request.sid, data))

    if 'state' in data and data['state'].isdigit():                                  
        relay1_state = int(data['state']) # data comes in as a str.
        if relay1_state == 0:
            relay1.off()
        else:
            relay1.on()
        logger.info("Relay 1 is " + str(relay1.value))

    # Broadcast new state to *every* connected connected (so they remain in sync).
    emit("relay1", relay1.value, broadcast=True)                                               

# LED2 Handler
@socketio.on('relay2')                                                                  
def handle_state(data):                                                              
    logger.info("Update on Relay 2 from client {}: {} ".format(request.sid, data))

    if 'state' in data and data['state'].isdigit():                                  
        relay2_state = int(data['state']) # data comes as a str.
        if relay2_state == 0:
            relay2.off()
        else:
            relay2.on()
        logger.info("Relay 2 is " + str(relay2.value))

    # Broadcast new state to *every* connected connected (so they remain in sync).
    emit("relay2", relay2.value, broadcast=True)                                               


if __name__ == '__main__':

    socketio.run(app, host='0.0.0.0', debug=True)
    logger.info("Temp " + str(dht_sensor.read().temperature))