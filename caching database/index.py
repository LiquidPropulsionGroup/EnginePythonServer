from flask import Flask, abort
import redis as red
import serial, serial.tools.list_ports
import json, struct, sys
import threading

####* User defined variables START *####
try:
    sys.argv[1]
except IndexError:
    baudrate = 115200
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
    port = '/dev/controller_sensor'
else:
    port = sys.argv[2]

try:
    sys.argv[3]
except IndexError:
    stream_name = 'sensor_stream'
else:
    stream_name = sys.argv[3]
####! User defined variables END !####

# Flask app settings
app = Flask(__name__)

# Lock a thread
lock = threading.Lock()
serial_lock = threading.Lock()

# Loop control variable
CACHING = False

# Serial port settings
ser = serial.Serial(timeout=1)
ser.baudrate = baudrate
ser.port = port

# Opening serial port
ser.open()

# Creating redis client
redis = red.Redis(host='redis-database', port=6379)

# JSON Key list
Keys = [
        "PT_HE",
        "PT_Purge",
        "PT_Pneu",
        "PT_FUEL_PV",
        "PT_LOX_PV",
        #"PT_FUEL_INJ",
        "PT_CHAM",
        "TC_FUEL_PV",
        "TC_LOX_PV",
        "TC_LOX_Valve_Main",
        "TC_WATER_In",
        "TC_WATER_Out",
        "TC_CHAM",
        #"RC_LOX_Level",
        "FT_Thrust"
      ]

def run_app():
  app.run(host='0.0.0.0', port=3002, threaded=True)

def Cache():
    # Function for extracting uint16_t (2 bytes) data from the serial stream
    # Runs continuously while serial communication is present

    # Execution control variable is global
    global CACHING

    while True:
      # Empty loop waiting for CACHING = True
      if CACHING:
        print("LOOPING")
        # Flush the input buffer to get fresh data
        ser.reset_input_buffer()

        while ser.is_open == True:
          # Extract the next sequence of serial data until the terminator/starter packets
          serial_buffer = ser.read_until(b'\xFF\xFF\xFF\xFF\x00\x00\x00\x00')
          
          # Verify that the buffer is of the correct length
          BUFFER_LENGTH = 34

          if len(serial_buffer) == BUFFER_LENGTH:
            # Unpack the struct that is the serial message
            # Arduino is little-endian
            unpack_data = struct.unpack('<h h h h h h h h h h h h h d', serial_buffer)
            # Build the JSON with struct method
            data = {}
            for item in range(len(Keys)):
              data[Keys[item]] = str(unpack_data[item])
            #print(data)
            json_data = json.dumps(data)
            json_data = json.loads(json_data)		# Weird fix?

            # Then perform CRC TODO

            # Insert to redis
            if json_data:
              redis.xadd(stream_name, json_data)
              # print('Added to redis stream')        

            
          else:
            # If it is incorrect, discard the read and find another terminator
            print("=================")
            print(len(serial_buffer))
            print(serial_buffer)
            print("WRONG LENGTH - DISCARD")

@app.route('/serial/caching/<action>')
def caching_control(action):
  if action == 'START':
    try:
      ser.open()
    except serial.serialutil.SerialException:
      print('Port already open. Continuing...')
    print('ACTION START')
    #ser.flushInput()
    Cache()
  
  if action == 'CLOSE':
    # this might be a bad way to stop the program, causes shitpant
    ser.close()
    return 'Caching closed'

  return abort(404)

if __name__ == '__main__':
      # Threading the routes
      flaskApp_thread = threading.Thread(target=run_app)
      caching_thread = threading.Thread(target=Cache, args=[ser, redis, caching_stream_name, valve_stream_name])
      flaskApp_thread.start()
      caching_thread.start()
