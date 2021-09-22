from flask import Flask, abort
import redis as red
import serial, serial.tools.list_ports
import json, struct, sys, time

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

# JSON Key list
Keys = ["Timestamp",
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

def Cache():
    # Function for extracting uint16_t (2 bytes) data from the serial stream
    # Runs continuously while serial communication is present

    # Flush the input buffer to avoid overflow and get fresh data
    ser.reset_input_buffer()

    # Start the loop in the right place by finding a terminator character in the buffer
    serial_buffer = ser.read_until(b'\xFF\xFF\xFF\xFF\x00\x00\x00\x00')
    
    # Track the number of failed reads for debug
    count = 0
    while ser.is_open == True:
      print("=============")

      # Extract the next sequence of serial data until the terminator/starter packets
      serial_buffer = ser.read_until(b'\xFF\xFF\xFF\xFF\x00\x00\x00\x00')

      # Verify that the buffer is of the correct length
      BUFFER_LENGTH = 38

      if len(serial_buffer) == BUFFER_LENGTH:
        # Unpack the struct that is the serial message
        # Arduino is little-endian
        unpack_data = struct.unpack('<i h h h h h h h h h h h h h d', serial_buffer)

        # Build the JSON with struct method
        data = {}
        for item in range(len(Keys)):
          data[Keys[item]] = str(unpack_data[item])
        print(data)
        json_data = json.dumps(data)
        json_data = json.loads(json_data)		# Weird fix?

        # Then perform CRC TODO

        # Insert to redis
        if json_data:
          redis.xadd(stream_name, json_data)
          #print('Added to redis stream')        

        
      else:
        # If it is incorrect, discard the read and find another terminator
        count = count + 1
        print("Wrong Length: " + str(count))
           

      # count = count + 1
      # if count == 100:
      #       break

      # Collect individual bytes until the terminator sequence is found
      # Empty the buffer before doing this to make searching easier...
      # ser.reset_input_buffer()
      # One_Packet = True
      # while One_Packet == True:
      #       serial_buffer += ser.read()
      #       if 
      #print(int.from_bytes(b'\x03\x14\x00\x01',"little",signed=False))

    # #print('Run data extraction')
    # buffer = ''
    # json_object = None
    # while ser.is_open == True:
    #   #print('Serial is open:')
    #   #print(ser.readline())
    #   buffer+= ser.readline().decode('UTF-8')
    #   #print('Buffer reads:')
    #   #print(buffer)
    #   try:
    #     #print('loading JSON...')
    #     #print(buffer)
    #     #decoded_buffer = buffer.decode('UTF-8')
    #     #print(decoded_buffer)
    #     json_object = json.loads(buffer)
    #     #print(json_object)
    #     buffer = ''
    #     #print('The buffer is:')
    #     #print(buffer)
    #     #print(redis.xlen(stream_name))
    #     if json_object:
    #       redis.xadd(stream_name, json_object)
    #       print(json_object)
    #       print('Added to redis stream')
    #   except ValueError:
    #     #print('ValueError')
    #     #print(buffer)
    #     buffer = ''
        

    #   #message = ser.readline()
    #   #print(message)
    #   #decoded_message = message.decode('UTF-8')
    #   #print(decoded_message)
    #   #json_object = json.loads(decoded_message)
    #   #redis.xadd(stream_name, json_object)
    return 'Caching done'

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
    ser.close()
    return 'Caching closed'

  return abort(404)

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=3002, threaded=True)
