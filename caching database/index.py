from flask import Flask, abort
import redis as red
import serial
import json, sys, time

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

try:
    sys.argv[3]
except IndexError:
    stream_name = 'sensor'
else:
    stream_name = sys.argv[3]
####! User defined variables END !####

# Flask app settings
app = Flask(__name__)

# Serial port settings
ser = serial.Serial(timeout=1)
ser.baudrate = baudrate
ser.port = port

# Openning serial port
ser.open()

# Creating redis client
redis = red.Redis(host='redis-database', port=6379)

#Temp scope fix
#json_object = None

def something():
    #print('Run data extraction')
    buffer = ''
    json_object = None
    while ser.is_open == True:
      #print('Serial is open:')
      #print(ser.readline())
      buffer+= ser.readline().decode('UTF-8')
      #print(buffer)
      try:
        #print('loading JSON...')
        #print(buffer)
        #decoded_buffer = buffer.decode('UTF-8')
        #print(decoded_buffer)
        json_object = json.loads(buffer)
        #print(json_object)
        buffer = ''
        #print('The buffer is:')
        #print(buffer)
        #print(redis.xlen(stream_name))
        redis.xadd(stream_name, json_object)
        #print('added to redis stream')
      except ValueError:
        buffer = ''
        

      #message = ser.readline()
      #print(message)
      #decoded_message = message.decode('UTF-8')
      #print(decoded_message)
      #json_object = json.loads(decoded_message)
      #redis.xadd(stream_name, json_object)
    return 'Caching done'

@app.route('/serial/caching/<action>')
def caching_control(action):
  if action == 'START':
    print('action start')
    #ser.flushInput()
    something()
    print('action end')
  
  if action == 'CLOSE':
    ser.close()
    return 'Caching closed'

  return abort(404)

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=3002, threaded=True)
