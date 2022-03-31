import time
from flask import Flask, abort
import redis as red
import json, sys, sqlite3
import re
import threading

####* User defined variables START *####
try:
    sys.argv[1]
except IndexError:
    stream_name = 'sensor_stream' # default value
else:
    stream_name = sys.argv[1]
####! User defined variables END !####

# Flask app settings
app = Flask(__name__)

# Lock a thread
lock = threading.Lock()
serial_lock = threading.Lock()

# Flow control variable
STORING = False

# Creating redis client
redis = red.Redis(host='redis-database', port=6379)

def run_app():
    app.run(debug=False, host='0.0.0.0', port=3004, threaded=True)

def Store(redis):
    global STORING
    print("storing?")

    # Connect to the sqlite3 database
    connection = sqlite3.connect('./dat/database.db')
    print("db connected")

    # Establish the cursor to do operations on the .db
    cursor = connection.cursor()
    print("cursor created")

    # Creating the table to store data, if it doesn't exist already
    # create_table stores the SQL command to be executed by cursor
    create_table = f""" CREATE TABLE IF NOT EXISTS {stream_name}
    ( Timestamp varchar(255),
    PT_HE varchar(255),
    PT_Purge varchar(255),
    PT_Pneu varchar(255),
    PT_FUEL_PV varchar(255),
    PT_LOX_PV varchar(255),
    PT_CHAM varchar(255),
    TC_FUEL_PV varchar(255), 
    TC_LOX_PV varchar(255),
    TC_LOX_Valve_Main varchar(255),
    TC_WATER_In varchar(255),
    TC_WATER_Out varchar(255),
    TC_CHAM varchar(255),
    FT_Thrust varchar(255));"""
    # Create the table
    cursor.execute(create_table)
    # Commit changes to the .db
    connection.commit()
    print("table created")

    # Get the first item in the stream to use XREAD
    data = redis.xrange(stream_name, count=1)
    (label, data) = data[0]
    # print(label)
    # print(data)

    # Use XREAD to get the first set of data
    data = redis.xread({ stream_name: f'{label.decode()}' }, block = 0)
    (label, data) = data[0]
    # print(label)
    # print(data)

    # Entering the storage loop for as long as operation is true
    while True:
        # Empty while loop waiting for STORING = true
        print("looping", flush=True)
        if STORING:
            print("storing")
            for sensor_reading in data:
                # Separate the tuples
                (sensor_label, sensor_data) = sensor_reading
                print(sensor_label)
                print(sensor_data)

                # Split the redis timestamp using regex
                [sensor_timestamp, multiInsertID] = re.split("-", sensor_label.decode())
                # print(sensor_timestamp)
                # print(sensor_data[b'PT_HE'].decode())
                # print(sensor_data[b'PT_Purge'].decode())
                # print(sensor_data[b'PT_Pneu'].decode())
                # print(sensor_data[b'PT_FUEL_PV'].decode())
                # print(sensor_data[b'PT_LOX_PV'].decode())
                # print(sensor_data[b'PT_CHAM'].decode())
                # print(sensor_data[b'TC_FUEL_PV'].decode())
                # print(sensor_data[b'TC_LOX_PV'].decode())
                # print(sensor_data[b'TC_LOX_Valve_Main'].decode())
                # print(sensor_data[b'TC_WATER_In'].decode())
                # print(sensor_data[b'TC_WATER_Out'].decode())
                # print(sensor_data[b'TC_CHAM'].decode())
                # print(sensor_data[b'FT_Thrust'].decode())


                # Write the SQL command to add the data to the .db
                insert_string = f""" INSERT INTO {stream_name} (PT_HE, PT_Purge, PT_Pneu, PT_FUEL_PV, PT_LOX_PV, PT_CHAM, TC_FUEL_PV, TC_LOX_PV, TC_LOX_Valve_Main, TC_WATER_In, TC_WATER_Out, FT_Thrust) VALUES 
                ( {sensor_timestamp[0]},
                {sensor_data[b'PT_HE'].decode()},
                {sensor_data[b'PT_Purge'].decode()},
                {sensor_data[b'PT_Pneu'].decode()},
                {sensor_data[b'PT_FUEL_PV'].decode()},
                {sensor_data[b'PT_LOX_PV'].decode()},
                {sensor_data[b'PT_CHAM'].decode()},
                {sensor_data[b'TC_FUEL_PV'].decode()},
                {sensor_data[b'TC_LOX_PV'].decode()},
                {sensor_data[b'TC_LOX_Valve_Main'].decode()},
                {sensor_data[b'TC_WATER_In'].decode()},
                {sensor_data[b'TC_WATER_Out'].decode()},
                {sensor_data[b'TC_CHAM'].decode()},
                {sensor_data[b'FT_Thrust'].decode()} );"""
                print("insert command generated")
                print(insert_string)
                
                # Execute the SQL command
                cursor.execute(insert_string)
                print("insert command executed")

                # Commit changes
                connection.commit()
                print("insert committed")

            # Find the next set of redis data
            data = redis.xrange(stream_name, min=f'{sensor_label.decode()}', count=1)
            (label, data) = data[0]
            data = redis.xread({ stream_name: f'{label.decode()}' }, block = 0)
            (label, data) = data[0]
            print("new data found")
        
        time.sleep(3)


@app.route('/serial/storage/<action>')
def storage_control(action):
    global STORING
    if action == 'START':
        print('STORAGE START')

        # Start the infinite loop of pulling and storing data
        with lock:
            STORING = True

        # This should never execute, it would mean storage has crashed
        return 'Storage started'

    if action == 'CLOSE':
        print('STORAGE CLOSE')
        # Stop the storage loop
        with lock:
            STORING = False
        
        # Indicate storage stopped
        return 'Storage closed'

    return abort(404)

if __name__ == '__main__':
    # Threading the routes
    flaskApp_thread = threading.Thread(target=run_app)
    storing_thread = threading.Thread(target=Store, args=[redis])
    flaskApp_thread.start()
    storing_thread.start()
