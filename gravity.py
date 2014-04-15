import os

from decimal import Decimal

from flask import Flask
from pymongo import MongoClient, GEOSPHERE
from restless.fl import FlaskResource
from wolfram import WolframAlphaDataSource

app = Flask(__name__)

APP_ID = os.getenv('APP_ID')
DEBUG = 'DEBUG' in os.environ and os.environ['DEBUG'] == 'True'


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
            if cached.count() > 0:
                return cached[0]
        except:
            pass

        wolfram_source = WolframAlphaDataSource(APP_ID)
        acceleration, source = \
            wolfram_source.get_gravitational_acceleration_at_point(
                location['coordinates'][1], location['coordinates'][0])

        result = {
            'acceleration': acceleration,
            'location': location,
            'source': source,
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
