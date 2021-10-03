from flask import Flask, abort, request
from flask_cors import CORS
import redis as red
import serial, serial.tools.list_ports
import json, struct, sys, time
import threading

####* DEFAULT ARGUMENTS *####
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
    #ports = serial.tools.list_ports.comports()
    #print(ports)
    #com_list = []
    #for p in ports:
    #      com_list.append(p.device)
    #print(com_list)
    #port = com_list[1]
    #print(port)

    # For use in live environment
    port = '/dev/controller_valve' # defult value
else:
    port = sys.argv[2]

try:
    sys.argv[3]
except IndexError:
    caching_stream_name = "sensor_stream"
else:
    caching_stream_name = sys.argv[3]

try:
    sys.argv[4]
except IndexError:
    valve_stream_name = "valve_stream"
else:
    valve_stream_name = sys.argv[4]
####* END DEFAULT ARGUMENTS *####

# Flask app setup
app = Flask(__name__)
CORS(app) # Enables POST requests

# Lock a thread
lock = threading.Lock()
serial_lock = threading.Lock()

# Creating redis client instance
redis = red.Redis(host='redis-database', port=6379)

# Loop control variable
CACHING = False

# Serial port setup
ser = serial.Serial(timeout=1)
ser.baudrate = baudrate
ser.port = port
ser.open()

# JSON Key list for sensor data
Sensor_Keys = [
    "Timestamp",
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
    "FT_Thrust",
    "FL_WATER"
]

# JSON Key list for valve status
Valve_Keys = [
    "Timestamp",
    "FUEL_Press",
    "LOX_Press",
    "FUEL_Vent",
    "LOX_Vent",
    "MAIN",
    "FUEL_Purge",
    "LOX_Purge",
]

def run_app():
    app.run(debug=False, threaded=True, host='0.0.0.0', port=3005)

def Cache(ser, redis, caching_stream_name, valve_stream_name):
    # Function for sorting out which type of message is being received
    global CACHING

    # Sensor serial messages are of length 40 bytes
    SENSOR_BUFFER_LENGTH = 40
    # Valve serial messages are of length 19 bytes
    VALVE_BUFFER_LENGTH = 19

    # Flush the input buffer to avoid overflow and get fresh data
    ser.reset_input_buffer()

    # Both are padded with a starter sequence of 4 zero bytes
    # and terminated with a sequence of 4 max bytes
    # Start the loop in the right place by finding a terminator string in the buffer
    # serial_buffer = ser.read_until(b'\xFF\xFF\xFF\xFF\x00\x00\x00\x00')

    while True:
        if CACHING:
            #print("LOOPING")
            # Extract the next sequence of serial data until the terminator/starter packets
            serial_buffer = ser.read_until(b'\xFF\xFF\xFF\xFF\x00\x00\x00\x00')
            #print(serial_buffer)
            # If the serial buffer has a length of 40 bytes, it is a sensor data package
            if len(serial_buffer) == SENSOR_BUFFER_LENGTH:
                # Unpack the struct that is the serial message
                # Arduino is little-endian
                unpack_data = struct.unpack('<i h h h h h h h h h h h h h h d', serial_buffer)
                # Build the JSON with struct method
                data = {}
                for item in range(len(Sensor_Keys)):
                    data[Sensor_Keys[item]] = str(unpack_data[item])
                #print(data)
                json_data = json.dumps(data)
                json_data = json.loads(json_data)		# Weird fix?

                # Insert to redis
                if json_data:
                    redis.xadd(caching_stream_name, json_data)
                    # print("Added to redis stream")

            elif len(serial_buffer) == VALVE_BUFFER_LENGTH:
                # Unpack the struct that is the serial message
                # Arduino is little-endian
                # Unpack the struct that is the serial message
                # Arduino is little-endian
                unpack_data = struct.unpack('<i b b b b b b b d', serial_buffer)
                print(unpack_data)
                # Build the JSON with struct method
                data = {}
                for item in range(len(Valve_Keys)):
                    data[Valve_Keys[item]] = str(unpack_data[item])
                print(data)
                json_data = json.dumps(data)
                json_data = json.loads(json_data)		# Weird fix?
                print(json_data)

                # Insert to redis
                if json_data:
                    redis.xadd(valve_stream_name, json_data)
                    print("Added to redis stream")

            else:
                # If the buffer length is improper, the message is invalid and should be discarded
                print("=====INVALID MESSAGE=====")
                print(serial_buffer)
        # else:
            # print("Not caching...")

def compose_pair(key, state, instruction):
    if key == Valve_Keys[1]:
        leadByte = b'\x53'    # FUEL_Pres(S)
    elif key == Valve_Keys[2]:
        leadByte = b'\x73'    # FUEL_Pres(s)
    elif key == Valve_Keys[3]:
        leadByte = b'\x54'    # FUEL_Ven(T)
    elif key == Valve_Keys[4]:
        leadByte = b'\x74'    # LOX_Ven(t)
    elif key == Valve_Keys[5]:
        leadByte = b'\x4D'    # (M)ain
    elif key == Valve_Keys[6]:
        leadByte = b'\x45'    # FUEL_Purg(E)
    elif key == Valve_Keys[7]:
        leadByte = b'\x65'    # FUEL_Purg(e)

    if state == True:
        stateByte = b'\x31'   # True (1)
    elif state == False:
        stateByte = b'\x30'   # False (0)

    instruction += leadByte + stateByte
    return instruction

if __name__ == "__main__":
    # Threading the routes
    flaskApp_thread = threading.Thread(target=run_app)
    caching_thread = threading.Thread(target=Cache, args=[ser, redis, caching_stream_name, valve_stream_name])
    flaskApp_thread.start()
    caching_thread.start()


@app.route('/serial/caching/START')
def cachingStart():
    try: 
        ser.open()
    except serial.serialutil.SerialException:
        print('Port already open. Continuing...')
    print('ACTION START')
    # Begin pumping data into the redis database
    global CACHING
    with lock:
        CACHING = True
    # This unblocks the Cache() while loop
    return 'Caching Started'


@app.route('/serial/caching/STOP')
def cachingStop():
    global CACHING
    with lock:
        CACHING = False
    # ser.close()
    return 'Caching Closed'

# Defining the valve data caching route
# Has two options...
# POST: sends a command downstream to the Arduino to execute
# GET: polls the Arduino for the current status
@app.route('/serial/valve/update', methods=['POST', 'GET'])
def serialSend():
    print("ROUTE REACHED")
    print(request.method)
    if request.method == 'POST':
        # Command is sent in as a JSON object
        message = request.get_json(force=True)
        print(message)
        # Instruction starter character '<'
        instruction = b'\x3C'
        # Pull the items out of the JSON object using the key list
        for key in Valve_Keys[1:]:
            print(key)
            print(int(message[key]))
            # Pair up the keys and the instruction values
            instruction = compose_pair(key,message[key],instruction)
        # Instruction terminator character '>'
        instruction += b'\x3E'
        ser.write(instruction)
        print(instruction)

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

    return "Message Sent"
