from flask import Flask, abort
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
    ports = serial.tools.list_ports.comports()
    print(ports)
    com_list = []
    for p in ports:
          com_list.append(p.device)
    print(com_list)
    # port = '/dev/controller_sensor' # defult value
    port = com_list[1]
    print(port)
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

#Temp scope fix
#json_object = None

def Cache():
    # Function for extracting uint16_t (2 bytes) data from the serial stream
    # Runs continuously while serial communication is present

    # Flush the input buffer to avoid overflow and get fresh data
    ser.reset_input_buffer()

    # Start the loop in the right place by finding a terminator character in the buffer
    serial_buffer = ser.read_until(b'\xFF\xFF\xFF\xFF\x00\x00\x00\x00')
    count = 0
    while ser.is_open == True:
      print("==============")
      print(count)
      # Extract the next sequence of serial data until the terminator
      serial_buffer = ser.read_until(b'\xFF\xFF\xFF\xFF\x00\x00\x00\x00')
      print(serial_buffer)
      # Verify that the buffer is of the correct length
      BUFFER_LENGTH = 38
      if len(serial_buffer) == BUFFER_LENGTH:
        # If it is correct, slice the buffer
        TimeStamp = serial_buffer[0:4]
        PT_HE = serial_buffer[4:6]
        PT_Purge = serial_buffer[6:8]
        PT_Pneu = serial_buffer[8:10]
        PT_FUEL_PV = serial_buffer[10:12]
        PT_LOX_PV = serial_buffer[12:14]
        #PT_FUEL_INJ = serial_buffer[14:16]
        PT_CHAM = serial_buffer[14:16]
        TC_FUEL_PV = serial_buffer[16:18]
        TC_LOX_PV = serial_buffer[18:20]
        TC_LOX_Valve_Main = serial_buffer[20:22]
        TC_WATER_In = serial_buffer[22:24]
        TC_WATER_Out = serial_buffer[24:26]
        TC_CHAM = serial_buffer[26:28]
        #RC_LOX_Level = serial_buffer[30:32]
        FT_Thrust = serial_buffer[28:30]
        Terminator = serial_buffer[30:38]

        # Process bytes into ints
        TimeStamp_int = int.from_bytes(TimeStamp,"little",signed=False)
        PT_HE_int = int.from_bytes(PT_HE,"little",signed=False)
        PT_Purge_int = int.from_bytes(PT_Purge,"little",signed=False)
        PT_Pneu_int = int.from_bytes(PT_Pneu,"little",signed=False)
        PT_FUEL_PV_int = int.from_bytes(PT_FUEL_PV,"little",signed=False)
        PT_LOX_PV_int = int.from_bytes(PT_LOX_PV,"little",signed=False)
        #PT_FUEL_INJ_int = int.from_bytes(PT_FUEL_INJ,"little",signed=False)
        PT_CHAM_int = int.from_bytes(PT_CHAM,"little",signed=False)
        TC_FUEL_PV_int = int.from_bytes(TC_FUEL_PV,"little",signed=False)
        TC_LOX_PV_int = int.from_bytes(TC_LOX_PV,"little",signed=False)
        TC_LOX_Valve_Main_int = int.from_bytes(TC_LOX_Valve_Main,"little",signed=False)
        TC_WATER_In_int = int.from_bytes(TC_WATER_In,"little",signed=False)
        TC_WATER_Out_int = int.from_bytes(TC_WATER_Out,"little",signed=False)
        TC_CHAM_int = int.from_bytes(TC_CHAM,"little",signed=False)
        #RC_LOX_Level_int = int.from_bytes(RC_LOX_Level,"little",signed=False)
        FT_Thrust_int = int.from_bytes(FT_Thrust,"little",signed=False)

        # Build the JSON object
        data = {}
        data[Keys[0]] = TimeStamp_int
        data[Keys[1]] = PT_HE_int
        data[Keys[2]] = PT_Purge_int
        data[Keys[3]] = PT_Pneu_int
        data[Keys[4]] = PT_FUEL_PV_int
        data[Keys[5]] = PT_LOX_PV_int
        data[Keys[6]] = PT_CHAM_int
        data[Keys[7]] = TC_FUEL_PV_int
        data[Keys[8]] = TC_LOX_PV_int
        data[Keys[9]] = TC_LOX_Valve_Main_int
        data[Keys[10]] = TC_WATER_In_int
        data[Keys[11]] = TC_WATER_Out_int
        data[Keys[12]] = TC_CHAM_int
        data[Keys[13]] = FT_Thrust_int
        json_data = json.dumps(data)
        print(json_data)

        # Insert to redis
        # if json_data:
        #   redis.xadd(stream_name, json_data)
        #   print(json_data)
        #   print('Added to redis stream')        

        # Then perform CRC TODO
      else:
        # If it is incorrect, discard the read and find another terminator
        print("Wrong Length")    

      count = count + 1
      if count == 100:
            break

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
