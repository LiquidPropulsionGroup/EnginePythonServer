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
redis = red.Redis(host='redis-database', port=6379)

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
    connection.commit()
    tracking = 0
    # Getting first item from stream to properly use XREAD
    data = redis.xrange(stream_name, count=1)
    #print('Getting first item for ranging:')
    #print(data)
    (label, data) = data[0]
    #print('Label and data of first item:')
    #print(label)
    #print(data)
    # Getting the first set of XREAD data and decoupling the tuple for databasing
    print('Grabbing the first dataset...')
    data = redis.xread({ stream_name: f'{label.decode()}' }, block=0)
    #print(data)
    (label, data) = data[0]
    #print(data)
    # Entering databasing loop that can only close if global variable 'operation' is set to False
    while operation == True:
      for sensor_reading in data:
        print('Trying to read new data')
        try:
          (label, reading) = sensor_reading
          #print(label)
          #print(reading)
        except ValueError:
          print('Failed to get sensor_reading')
        else:
          print('New read:')
          print(label)
          print(reading)
          #print('^^^ READING ^^^')
          if reading:
            print('Inserting DATA to SQL table')
            #print(label)
            #print(reading)
            try:
              cursor.execute(f"INSERT INTO {stream_name} VALUES ({label.decode()}, {reading[b'PT_HE'].decode()}, {reading[b'PT_Purge'].decode()}, {reading[b'PT_Pneu'].decode()}, {reading[b'PT_FUEL_PV'].decode()}, {reading[b'PT_LOX_PV'].decode()}, {reading[b'PT_FUEL_INJ'].decode()}, {reading[b'PT_CHAM'].decode()}, {reading[b'TC_FUEL_PV'].decode()}, {reading[b'TC_LOX_PV'].decode()}, {reading[b'TC_LOX_Valve_Main'].decode()}, {reading[b'RC_LOX_Level'].decode()}, {reading[b'FT_Thrust'].decode()})")
              connection.commit()
              tracking += 1
              print(tracking)
              print('==============================INSERTED DATA=============================')
            #(numberofrows,) = cursor.fetchone()
              print('SQL TABLE ROWS:')
              cursor.execute(f"SELECT * FROM {stream_name}")
              print(len(cursor.fetchall()))
            except KeyError:
              print('KeyError, malformed input, discarded')
            except ValueError:
              print('ValueError, malformed input, discarded')
          #elif not reading:
          #  print('Reading is empty, waiting...')
          #  break
          #else:
          #  print('Something happened')
          #  break
      data = redis.xrange(stream_name, min=f'{label.decode()}', count=1)
      (label, data) = data[0]
      print('Trying to read new data chunk')
      data = redis.xread({ stream_name: f'{label.decode()}' }, block=0)
      print('Unblocked')
      (label, data) = data[0]
      #print(data)
    # Send message to confirm finished databasing
    return 'Storage done'

  if action == 'CLOSE':
    # Setting 'operation' variable to False to stop databasing from redis cache
    operation = False
    return 'Storage closed'

  return abort(404)

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=3004, threaded=True)
