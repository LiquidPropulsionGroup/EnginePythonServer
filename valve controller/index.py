from flask import Flask, abort, request
import redis as red
import serial, serial.tools.list_ports
import json, struct, sys, time

####* User defined variables START *####
try:
    sys.argv[1]
except IndexError:
    baudrate = 115200 # defult value
else:
    baudrate = sys.argv[1]

try:
    sys.argv[2]
except IndexError:
    # For use in desktop environment:
    # ports = serial.tools.list_ports.comports()
    # print(ports)
    # com_list = []
    # for p in ports:
    #       com_list.append(p.device)
    # print(com_list)
    # port = com_list[1]
    # print(port)

    # For use in live environment
    port = '/dev/controller_valve' # defult value
else:
    port = sys.argv[2]

try:
    sys.argv[3]
except IndexError:
    stream_name = 'valve_stream'
else:
    stream_name = sys.argv[3]
####! User defined variables END !####

# Flask app settings
app = Flask(__name__)

# Serial port settings
ser = serial.Serial(timeout=1)
ser.baudrate = baudrate
ser.port = port

# Opening serial port
ser.open()

# Creating redis client
redis = red.Redis(host='redis-database', port=6379)

# One URL to build a complete serial message containing all desired valve states from ui
@app.route('/serial/valve/update', methods= ['POST', 'GET'])
def press_valve_route(action):
  if request.method == 'POST':
    # Data comes from UI as JSON
    message = request.json()
    print(message)


    return abort(404)

# One URL to build a complete serial message containing all desired valve states from manual input

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=3003, threaded=True)      