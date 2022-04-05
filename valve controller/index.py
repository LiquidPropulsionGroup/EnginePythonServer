from flask import Flask, abort, request
from flask_cors import CORS
import redis as red
import serial, serial.tools.list_ports
import json, struct, sys

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

eventDB_name = 'event_stream'

# Serial port settings
ser = serial.Serial(timeout=1)
ser.baudrate = baudrate
ser.port = port

# Flask app settings
app = Flask(__name__)
# To enable POST requests
CORS(app)

# Creating redis client
redis = red.Redis(host='redis-database', port=6379)

# Keylist
KeyList = [
  "FUEL_Press",
  "LOX_Press",
  "FUEL_Vent",
  "LOX_Vent",
  "MAIN",
  "FUEL_Purge",
  "LOX_Purge",
]

def convert(obj):
    if isinstance(obj, bool):
        return str(obj).lower()
    if isinstance(obj, (list, tuple)):
        return [convert(item) for item in obj]
    if isinstance(obj, dict):
        return {convert(key):convert(value) for key, value in obj.items()}
    return obj

def padOut():
    # Create empty elements
    padding = {}
    for n in len(KeyList):
          name = KeyList[n]
          padding = {**padding, **{name:'?'}}
    return padding

def compose_pair(key, state, instruction):
  if key == KeyList[0]:
    leadByte = b'\x53'    # FUEL_Pres(S)
  elif key == KeyList[1]:
    leadByte = b'\x73'    # LOX_Pres(S)
  elif key == KeyList[2]:
    leadByte = b'\x54'    # FUEL_Ven(T)
  elif key == KeyList[3]:
    leadByte = b'\x74'    # LOX_Ven(t)
  elif key == KeyList[4]:
    leadByte = b'\x4D'    # (M)ain
  elif key == KeyList[5]:
    leadByte = b'\x45'    # FUEL_Purg(E)
  elif key == KeyList[6]:
    leadByte = b'\x65'    # LOX_Purg(e)

  if state == True:
    stateByte = b'\x31'   # True (1)
  elif state == False:
    stateByte = b'\x30'   # False (0)

  instruction += leadByte + stateByte
  return instruction

# One URL to build a complete serial message containing all desired valve states from ui
@app.route('/serial/valve/update', methods= ['POST', 'GET'])
def valve_update():
  print("ROUTE REACHED", flush=True) # WEIRD FIX ALERT
  #print("???")
  try:
    # Opening serial port
    ser.open()
    #ser.close()
    #ser.open()
  except:
    print("Already open...")
  print(request.method)

  if request.method == 'POST':
    # Data comes from UI as JSON
    message = request.get_json(force=True)
    # print(request.content_type)
    print("RECEIVED POST REQUEST")
    print(message)
    # Build the instruction message
    instruction = b'\x3C'   # Starter character '<'
    for key in KeyList:
      # print(key)
      # print(int(message[key]))
      instruction = compose_pair(key,message[key],instruction)
    instruction += b'\x3E'  # Terminator character '>'

    # Send the instruction message
    ser.write(instruction)
    print(instruction)

    # Generate event message dict
    message = json.loads(json.dumps(convert(message)))
    print(message)
    event_data = {'EVENT':'POST'}
    event_data = {**event_data, **message}
    redis.xadd(eventDB_name,event_data)
    
  
  if request.method == 'GET':
    # Generate a polling message for the Arduino
    # A string of same length as the instruction message for simplicity
    status_request_char = b'\x3F'
    status_request = b'\x3C'
    for i in range(0,14):
        status_request += status_request_char
    status_request += b'\x3E'
    ser.write(status_request)
    print(status_request)

    # Generate event message dict
    message = padOut()
    print(message)
    event_data = {'EVENT':'POLL'}
    event_data = {**event_data, **message}
    redis.xadd(eventDB_name,event_data)
    

  #ser.reset_input_buffer()
  print("AWAIT RESPONSE")
  serial_buffer = ser.read_until(b'\xFF\xFF\xFF\xFF')
  print(serial_buffer)

  # Verify that the buffer is of the correct length
  BUFFER_LENGTH = 15

  if len(serial_buffer) == BUFFER_LENGTH:
    # Unpack the struct that is the serial message
    # Arduino is little-endian
    unpack_data = struct.unpack('<I b b b b b b b I', serial_buffer)
    #print(unpack_data)
    # Build the JSON with struct method
    data = {}
    for item in range(len(KeyList)):
      data[KeyList[item]] = str(unpack_data[item+1])
      
    # print(data)
    json_data = json.dumps(data)
    json_data = json.loads(json_data)		# Weird fix?
    print(json_data)

    # Insert to redis
    if json_data:
      print
      event_data = {'EVENT':'RESPONSE'}
      event_data = {**event_data, **json_data}
      redis.xadd(eventDB_name, event_data)
      redis.xadd(stream_name, json_data)
      # print('Added to redis stream')
      print("Reply:")
      print(json_data)
      return json_data

  return "Sent + Received"

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=3003)      
