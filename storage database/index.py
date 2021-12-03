from flask import Flask, abort
import redis as red
import json, sys, sqlite3
import re

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

# Creating redis client
redis = red.Redis(host='redis-database', port=6379)

def Store():
    global operation

    # Connect to the sqlite3 database
    connection = sqlite3.connect('database.db')
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
    FT_Thrust varchar(255),
    FL_WATER varchar(255) );"""
    # Create the table
    cursor.execute(create_table)
    # Commit changes to the .db
    connection.commit()
    print("table created")

    # Get the first item in the stream to use XREAD
    data = redis.xrange(stream_name, count=1)
    (label, data) = data[0]
    print(label)
    print(data)

    # Use XREAD to get the first set of data
    data = redis.xread({ stream_name: f'{label.decode()}' }, block = 0)
    (label, data) = data[0]
    #print(label)
    #print(data)

    # Entering the storage loop for as long as operation is true
    while operation == True:
        print("looping...")
        for sensor_reading in data:
            # Separate the tuples
            (sensor_label, sensor_data) = sensor_reading
            #print(sensor_label)
            #print(sensor_data)

            # Split the redis timestamp using regex
            sensor_timestamp = re.split("-", sensor_label.decode())
            print(sensor_timestamp)

            # Write the SQL command to add the data to the .db
            insert_string = f""" INSERT INTO {stream_name} VALUES 
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
            {sensor_data[b'FT_Thrust'].decode()},
            {sensor_data[b'FL_WATER'].decode()} );"""
            print("insert command generated")

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


@app.route('/serial/storage/<action>')
def storage_control(action):
    if action == 'START':
        print('STORAGE START')
        global operation
        operation = True

        # Start the infinite loop of pulling and storing data
        Store()

        # This should never execute, it would mean storage has crashed
        return 'Storage crashed'

    if action == 'CLOSE':
        operation = False

        # Indicate storage stopped
        return 'Storage closed'

    return abort(404)

# Flow control variable
global operation
operation = False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3004, threaded=True)
