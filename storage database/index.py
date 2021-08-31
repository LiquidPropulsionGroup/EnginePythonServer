from flask import Flask, abort
import redis as red
import json, sys, sqlite3

####* User defined variables START *####
try:
    sys.argv[1]
except IndexError:
    stream_name = 'sensor' # defult value
else:
    stream_name = sys.argv[1]
####! User defined variables END !####

# Flask app settings
app = Flask(__name__)

# Creating redis client
redis = red.Redis(host='127.0.0.1', port=6379)

# Global variable for control structure
operation = True

@app.route('/serial/storage/<action>')
def storage_control(action):
  """Route for initalizing Storage Backup

  Arguments:
      action {string} -- User Defined state that initiates/stops storage backup.

  Returns:
      string -- Returns a confirmation of a finished process.
  """
  if action == 'START':
    # Changing global variabel to initalize loop
    operation = True
    # Connecting sqlite database
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()
    # Creating tabe storing engine data
    create_table = f""" CREATE TABLE IF NOT EXISTS {stream_name} 
    ( Time varchar(255), 
    PT_HE varchar(255), 
    PT_Purge varchar(255), 
    PT_Pneu varchar(255), 
    PT_FUEL_PV varchar(255), 
    PT_LOX_PV varchar(255), 
    PT_FUEL_INJ varchar(255), 
    PT_CHAM varchar(255), 
    TC_FUEL_PV varchar(255), 
    TC_LOX_PV varchar(255), 
    TC_LOX_Valve_Main varchar(255), 
    RC_LOX_Level varchar(255), 
    FT_Thrust varchar(255)); """
    cursor.execute(create_table)
    # Getting first item from stream to properly use XREAD 
    data = redis.xrange(stream_name, count=1)
    #print(data)
    (label, data) = data[0]
    # Getting the first set of XREAD data and decoupling the tuple for databasing
    data = redis.xread({ stream_name: f'{label.decode()}' }, block=0)
    (label, data) = data[0]
    #print(data)
    # Entering databasing loop that can only close if global variable 'operation' is set to False
    while operation == True:
      for sensor_reading in data:
        #print(sensor_reading)
        (label, reading) = sensor_reading
        #print('Label and reading:')
        #print(label)
        #print(reading)
        cursor.execute(f"INSERT INTO {stream_name} VALUES ({label.decode()}, {reading[b'PT_HE'].decode()}, {reading[b'PT_Purge'].decode()}, {reading[b'PT_Pneu'].decode()}, {reading[b'PT_FUEL_PV'].decode()}, {reading[b'PT_LOX_PV'].decode()}, {reading[b'PT_FUEL_INJ'].decode()}, {reading[b'PT_CHAM'].decode()}, {reading[b'TC_FUEL_PV'].decode()}, {reading[b'TC_LOX_PV'].decode()}, {reading[b'TC_LOX_Valve_Main'].decode()}, {reading[b'RC_LOX_Level'].decode()}, {reading[b'FT_Thrust'].decode()})")
        #cursor.execute(f"INSERT INTO {stream_name} VALUES (
      data = redis.xread({ stream_name: f'{label.decode()}' }, block=0)
    # Send message to confirm finished databasing
    return 'Storage done'

  if action == 'CLOSE':
    # Setting 'operation' variable to False to stop databasing from redis cache
    operation = False
    return 'Caching closed'

  return abort(404)

if __name__ == '__main__':
      app.run(host='127.0.0.1', port=3004, threaded=True)
