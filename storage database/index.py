from flask import Flask, abort
import redis, json, sys, sqlite3

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
create_table = """
CREATE TABLE IF NOT EXISTS
engine()
"""
cursor.execute(create_table)

# Global variable for control structure
operation = True

# task: 
# - get first item id in stream to set XREAD correctly
# - idenity the id of the last item from dictinary being returned from XREAD
# - perform another XREAD and loop until client stops databasing
@app.route('/serial/storage/<action>')
def storage_control(action):
  if action == 'START':
    operation = True
    data = redis.xread({ stream_name: "- +" }, count=1)
    data = redis.xread({ stream_name: f'{data.id}' }, block=0) # might be diffrent also, needs to be done once
    while operation == True:
      data = redis.xread({ stream_name: f'{data.id_last}' }, block=0) # might be diffrent
      cursor.execute(f'INSERT INTO engine VALUES ()')
    return 'Storage done'

  if action == 'CLOSE':
    operation = False
    return 'Caching closed'

  return abort(404)

if __name__ == '__main__':
      app.run(host='192.168.0.11', port=3004)