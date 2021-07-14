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

@app.route('/stream')
def graph_data_route():
  def event_Stream():
    # Getting first item from stream to properly use XREAD 
    data = redis.xrange(stream_name, count=1)
    (label, data) = data
    # Getting the first set of XREAD data and decoupling the tuple for databasing
    data = redis.xread({ stream_name: f'{label.decode()}' }, block=0)
    (, data) = data
    # Entering infin loop
    while True:
      for sensor_reading in data:
        (label, reading) = data[sensor_reading]
        yield label + reading
        data = redis.xread({ stream_name: f'{label.decode()}' }, block=0)

  return Response(event_Stream(), mimetype="text/event-stream")

if __name__ == '__main__':
      app.run(host='192.168.0.11', port=3005, threaded=True)