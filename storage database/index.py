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
redis = red.Redis(host='192.168.0.11', port=6379)

# Connecting sqlite database
connection = sqlite3.connect('database.db')
cursor = connection.cursor()

# Creating tabe storing engine data
create_table = f"""
CREATE TABLE IF NOT EXISTS
{stream_name}(Time varchar(255), PT_HE varchar(255), PT_Purge varchar(255), PT_Pneu varchar(255), PT_FULE_PV varchar(255), PT_LOX_PV varchar(255), PT_FUEL_INJ varchar(255), PT_CHAM varchar(255), TC_FUEL_PV varchar(255), TC_LOX_PV varchar(255), TC_LOX_Valve_Main varchar(255), RC_LOX_Level varchar(255), FT_Thrust varchar(255))
"""
cursor.execute(create_table)

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
    # Getting first item from stream to properly use XREAD 
    data = redis.xrange(stream_name, count=1)
    (label, data) = data
    # Getting the first set of XREAD data and decoupling the tuple for databasing
    data = redis.xread({ stream_name: f'{label.decode()}' }, block=0)
    (label, data) = data
    # Entering databasing loop that can only close if global variable 'operation' is set to False
    while operation == True:
      for sensor_reading in data:
        (label, reading) = data[sensor_reading]
        cursor.execute(f'INSERT INTO engine VALUES ({label.decode()}, {data[b'PT_HE'].decode()}, {data[b'PT_Purge'].decode()}, {data[b'PT_Pneu'].decode()}, {data[b'PT_FULE_PV'].decode()}, {data[b'PT_LOX_PV'].decode()}, {data[b'PT_FUEL_INJ'].decode()}, {data[b'PT_CHAM'].decode()}, {data[b'TC_FUEL_PV'].decode()}, {data[b'TC_LOX_PV'].decode()}, {data[b'TC_LOX_Valve_Main'].decode()}, {data[b'RC_LOX_Level'].decode()}, {data[b'FT_Thrust'].decode()})')
      data = redis.xread({ stream_name: f'{label.decode()}' }, block=0)
    # Send message to confirm finished databasing
    return 'Storage done'

  if action == 'CLOSE':
    # Setting 'operation' variable to False to stop databasing from redis cache
    operation = False
    return 'Caching closed'

  return abort(404)

if __name__ == '__main__':
      app.run(host='192.168.0.11', port=3004, threaded=True)