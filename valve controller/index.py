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

@app.route('/serial/main/<action>')
def main_valve_route(action):
  if ser.is_open == True:
    if action == 'FUEL-MAIN-OPEN':
      ser.write(b'O5\n')
      message = ser.readline()
      return message.decode('UTF-8')

    if action == 'FUEL-MAIN-CLOSED':
      ser.write(b'F5\n')
      message = ser.readline()
      return message.decode('UTF-8')

    if action == 'LOX-MAIN-OPEN':
      ser.write(b'O6\n')
      message = ser.readline()
      return message.decode('UTF-8')

    if action == 'LOX-MAIN-CLOSED':
      ser.write(b'F6\n')
      message = ser.readline()
      return message.decode('UTF-8')

    return abort(404)

@app.route('/serial/press/<action>')
def press_valve_route(action):
  if ser.is_open == True:
    if action == 'FUEL-PRESS-OPEN':
      ser.write(b'O1\n')
      message = ser.readline()
      return message.decode('UTF-8')

    if action == 'FUEL-PRESS-CLOSED':
      ser.write(b'F1\n')
      message = ser.readline()
      return message.decode('UTF-8')

    if action == 'LOX-PRESS-OPEN':
      ser.write(b'O2\n')
      message = ser.readline()
      return message.decode('UTF-8')

    if action == 'LOX-PRESS-CLOSED':
      ser.write(b'F2\n')
      message = ser.readline()
      return message.decode('UTF-8')

    return abort(404)

@app.route('/serial/purge/<action>')
def purge_valve_route(action):
  if ser.is_open == True:
    if action == 'FUEL-PURGE-OPEN':
      ser.write(b'O7\n')
      message = ser.readline()
      return message.decode('UTF-8')

    if action == 'FUEL-PURGE-CLOSED':
      ser.write(b'F7\n')
      message = ser.readline()
      return message.decode('UTF-8')

    if action == 'LOX-PURGE-OPEN':
      ser.write(b'O8\n')
      message = ser.readline()
      return message.decode('UTF-8')

    if action == 'LOX-PURGE-CLOSED':
      ser.write(b'F8\n')
      message = ser.readline()
      return message.decode('UTF-8')

    return abort(404)

@app.route('/serial/vent/<action>')
def vent_valve_route(action):
  if ser.is_open == True:
    if action == 'FUEL-VENT-OPEN':
      ser.write(b'O3\n')
      message = ser.readline()
      return message.decode('UTF-8')

    if action == 'FUEL-VENT-CLOSED':
      ser.write(b'F3\n')
      message = ser.readline()
      return message.decode('UTF-8')

    if action == 'LOX-VENT-OPEN':
      ser.write(b'O4\n')
      message = ser.readline()
      return message.decode('UTF-8')

    if action == 'LOX-VENT-CLOSED':
      ser.write(b'F4\n')
      message = ser.readline()
      return message.decode('UTF-8')

    return abort(404)

if __name__ == '__main__':
      app.run(host='192.168.0.11', port=3001, threaded=True)      