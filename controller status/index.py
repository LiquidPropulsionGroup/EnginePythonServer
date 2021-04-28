from flask import Flask, abort
import serial, sys

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
    port = '/dev/controller_main' # defult value
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

@app.route('/serial/controller/<action>')
def main_controller_route(action):
  if ser.is_open == True:
    if action == 'STATUS':
      ser.write(b'STATUS\n')
      message = ser.readline()
      return message.decode('UTF-8')

    return abort(404)

if __name__ == '__main__':
      app.run(host='192.168.0.11', port=3003)