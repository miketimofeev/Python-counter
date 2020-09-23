import time
import argparse
from sqlalchemy import create_engine
from sqlalchemy import exc
from flask import Flask

parser = argparse.ArgumentParser()

parser.add_argument('--dbhost', help='PostgresqlDb host')
parser.add_argument('--dbname', help='PostgresqlDb name')
parser.add_argument('--dbusername', help='PostgresqlDb username')
parser.add_argument('--dbpassword', help='PostgresqlDb password')

args = parser.parse_args()

app = Flask(__name__)

connectionstring = "postgresql://{username}:{password}@{host}:5432/{db}".format(username=args.dbusername, password=args.dbpassword, host=args.dbhost, db=args.dbname)
retries = 30
while True:
    try:
        engine = create_engine(connectionstring)
        engine.connect()
        break
    except Exception as connectexc:
        if retries == 0:
            raise connectexc
        retries -= 1
        print("can't connect to DB '{db}' on host '{host}', will retry in 1 minute. Retries left {retries}.\nThe error is:\n".format(host=args.dbhost, db=args.dbname, retries=retries) + str(connectexc.orig))
        time.sleep(60)


engine.execute("CREATE TABLE IF NOT EXISTS counter (name text PRIMARY KEY, count text)") 
engine.execute("INSERT INTO counter (name) VALUES ('requests') ON CONFLICT (name) DO NOTHING")

def get_hit_count():
    retries = 5
    while True:
        try:
            result_query = engine.execute("SELECT count FROM counter WHERE name='requests'")  
            result = result_query.first()[0]
            if result is None:
                result = 0
            result = int(result) + 1
            sqlupdate = "UPDATE counter SET count={} WHERE name='requests'".format(result)
            engine.execute(sqlupdate)
            return result
        except Exception as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(1)

@app.route('/')
def hello():
    count = get_hit_count()
    return "Hey! You've visited me {} times.\n".format(count)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)