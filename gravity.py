import os
import wolframalpha

from datetime import datetime
from decimal import Decimal
from urllib import urlencode

from flask import Flask
from pymongo import MongoClient, GEOSPHERE
from restless.fl import FlaskResource

app = Flask(__name__)

APP_ID = os.getenv('APP_ID')
DEBUG = 'DEBUG' in os.environ and os.environ['DEBUG'] == 'True'

client = MongoClient(
    os.getenv('MONGOHQ_URL', 'mongodb://localhost:27017/gravity')
)
db = getattr(client, os.getenv('DATABASE_NAME', 'gravity'))
db.locations.ensure_index([('location', GEOSPHERE)])


class LocationResource(FlaskResource):
    fields = {
        'acceleration': 'acceleration',
        'location': 'location',
        'source': 'source',
    }

    def list(self):
        query = self.request.args.to_dict()

        location = {
            'type': 'Point',
            'coordinates': [Decimal(query['long']), Decimal(query['lat'])],
        }

        client = MongoClient(
            os.getenv('MONGOHQ_URL', 'mongodb://localhost:27017/gravity')
        )
        db = getattr(client, os.getenv('DATABASE_NAME', 'gravity'))
        db.locations.ensure_index([('location', GEOSPHERE)])

        location['coordinates'] = map(float, location['coordinates'])

        try:
            cached = db.locations.find({
                "location": {
                    "$nearSphere": location,
                    '$maxDistance': 500,
                }}).limit(1)
        except:
            pass
        else:
            if cached.count() > 0:
                return cached[0]

        client = wolframalpha.Client(APP_ID)
        wolfram_query = 'gravitational acceleration {} {}'.format(
            location['coordinates'][1],
            location['coordinates'][0])
        result = client.query(wolfram_query)
        pod = [
            pod.text for pod in result.pods
            if pod.text and pod.text.startswith('total field')
        ][0].split('\n')[0]
        acceleration = float(pod.split('|')[1].strip().split(' ')[0])

        result = {
            'acceleration': acceleration,
            'location': location,
            'source': {
                'Author/Site': 'Wolfram|Alpha',
                'Publisher': 'Wolfram Alpha LLC',
                'URL': 'http://api.wolframalpha.com/v2/query?{}'.format(
                    urlencode({'input': wolfram_query})),
                'Date': datetime.utcnow().isoformat(),
            }
        }

        try:
            db.locations.insert(result)
        except:
            pass

        return result

    def serialize(self, method, endpoint, data):
        return self.serialize_detail(data)

    def bubble_exceptions(self):
        return DEBUG


LocationResource.add_url_rules(app, '/api/v1/location/', 'location')

if __name__ == "__main__":
    app.run(debug=DEBUG)
