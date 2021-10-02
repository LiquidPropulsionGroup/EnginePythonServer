from flask import Flask, abort, request
from flask_cors import CORS
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
    ports = serial.tools.list_ports.comports()
    print(ports)
    com_list = []
    for p in ports:
          com_list.append(p.device)
    print(com_list)
    port = com_list[1]
    print(port)

    # For use in live environment
    # port = '/dev/controller_valve' # defult value
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
# To enable POST requests
CORS(app)

# Serial port settings
ser = serial.Serial(timeout=1)
ser.baudrate = baudrate
ser.port = port

# Opening serial port
ser.open()

# Creating redis client
redis = red.Redis(host='redis-database', port=6379)

# Keylist
KeyList = [
  "Packet_Start",
  "Timestamp",
  "FUEL_Press",
  "LOX_Press",
  "FUEL_Vent",
  "LOX_Vent",
  "MAIN",
  "FUEL_Purge",
  "LOX_Purge",
  "Packet_End"
]

def compose_pair(key, state, instruction):
  if key == KeyList[2]:
    leadByte = b'\x53'    # FUEL_Pres(S)
  elif key == KeyList[3]:
    leadByte = b'\x73'    # FUEL_Pres(S)
  elif key == KeyList[4]:
    leadByte = b'\x54'    # FUEL_Ven(T)
  elif key == KeyList[5]:
    leadByte = b'\x74'    # LOX_Ven(t)
  elif key == KeyList[6]:
    leadByte = b'\x4D'    # (M)ain
  elif key == KeyList[7]:
    leadByte = b'\x45'    # FUEL_Purg(E)
  elif key == KeyList[8]:
    leadByte = b'\x65'    # FUEL_Purg(e)

  if state == True:
    stateByte = b'\x31'   # True (1)
  elif state == False:
    stateByte = b'\x30'   # False (0)

  instruction += leadByte + stateByte
  return instruction
  


# One URL to build a complete serial message containing all desired valve states from ui
@app.route('/serial/valve/update', methods= ['POST', 'GET'])
def valve_update():
  print("ROUTE REACHED", flush=True)
  print(request.method)
  if request.method == 'POST':
    # Data comes from UI as JSON
    message = request.get_json(force=True)
    # print(request.content_type)
    print(message)
    instruction = b'\x3C'   # Starter character '<'
    for key in KeyList[2:9]:
      print(key)
      print(int(message[key]))
      instruction = compose_pair(key,message[key],instruction)

    instruction += b'\x3E'  # Terminator character '>'

    
    ser.write(instruction)
    print(instruction)
    
  
  # if request.method == 'GET':
  #   # Data comes from UI as JSON
  #   status_request_char = b'\x3F'
  #   status_request = ''
  #   for i in range(1,14): 
  #     status_request += status_request_char
  #   ser.write(status_request)


    ser.reset_input_buffer()
    print("AWAIT RESPONSE")
    serial_buffer = ser.read_until(b'\xFF\xFF\xFF\xFF')
    print(serial_buffer)
    # Extract the next sequence of serial data until the terminator/starter packets
    # serial_buffer = ser.read_until(b'\xFF\xFF\xFF\xFF\x00\x00\x00\x00')
    # print(serial_buffer)

    # Verify that the buffer is of the correct length
    BUFFER_LENGTH = 19

    if len(serial_buffer) == BUFFER_LENGTH:
      # Unpack the struct that is the serial message
      # Arduino is little-endian
      unpack_data = struct.unpack('<I i b b b b b b b I', serial_buffer)
      print(unpack_data)
      # Build the JSON with struct method
      data = {}
      for item in range(len(KeyList)):
        data[KeyList[item]] = str(unpack_data[item])
      print(data)
      json_data = json.dumps(data)
      json_data = json.loads(json_data)		# Weird fix?
      print(json_data)

      # Insert to redis
      # if json_data:
      #   redis.xadd(stream_name, json_data)
      #   print('Added to redis stream')   

    return "Sent + Received"

  
    
# One URL to build a complete serial message containing all desired valve states from manual input

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=3003, threaded=True)      