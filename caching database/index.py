from flask import Flask, abort
import serial, json, sys

####* User defined variables START *####
try:
    sys.argv[1]
except IndexError:
    baudrate = 9600 # defult value
else:
    baudrate = sys.argv[1]

try:
    sys.argv[2]
except IndexError:
    port = '/dev/controller_sensor' # defult value
else:
    port = sys.argv[2]
####! User defined variables END !####

# Flask app settings
app = Flask(__name__)

# Serial port settings
ser = serial.Serial()
ser.baudrate = baudrate
ser.port = port

# Openning serial port
ser.open()

# Creating redis client
redis = red.Redis(host='192.168.0.11', port=6379)

@app.route('/serial/caching/<action>')
def caching_control(action):
  if action == 'START':
    while ser.is_open == True:
      message = ser.readline()
      decoded_message = message.decode('UTF-8')
      json_object = json.loads(decoded_message)
      redis.xadd(stream_name, json_object)
    return 'Caching done'
  
  if action == 'CLOSE':
    ser.close()
    return 'Caching closed'

  return abort(404)

if __name__ == '__main__':
      app.run(host='192.168.0.11', port=3002)