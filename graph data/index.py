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

@app.route('/stream')
def graph_data_route():
  print('URL  reached')
  def event_Stream():
    print('Generating response_class')
    # Getting first item from stream to properly use XREAD 
    data = redis.xrange(stream_name, count=1)
    #print('Getting first item:')
    #print(data)
    (label, data) = data[0]
    #print('Label and data:')
    #print(label)
    #print(data)
    # Getting the first set of XREAD data and decoupling the tuple for databasing
    #print('Grabbing the first dataset...')
    data = redis.xread({ stream_name: f'{label.decode()}' }, block=0)
    print(data)
    (label, data) = data[0]
    # Entering infin loop
    while True:
      for sensor_reading in data:
        print('Sensor reading is:')
        print(sensor_reading)
        (label, reading) = sensor_reading
        print('Label and reading:')
        print(label)
        print(reading)
        # Transform redis stream json object to bytes
        string_label = label.decode('UTF-8')
        string_reading = { key.decode(): val.decode() for key, val in reading.items() }
        string_reading = json.dumps(string_reading)
        print('Strings are:')
        print(string_label)
        print(string_reading)
        yield string_label + string_reading
        print('======================NEW DATA GRAB=======================')
        data = redis.xread({ stream_name: f'{label.decode()}' }, block=0)
  # Return .response_class by calling the generator and extracting the yielded values
  return app.response_class(event_Stream(), mimetype="text/event-stream")

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=3005, threaded=True)
