import os

from decimal import Decimal

from flask import Flask
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

        wolfram_source = WolframAlphaDataSource(APP_ID)
        result = wolfram_source.get_gravitational_acceleration_at_point(
            location)

        return result

    def serialize(self, method, endpoint, data):
        return self.serialize_detail(data)

    def bubble_exceptions(self):
        return DEBUG


LocationResource.add_url_rules(app, '/api/v1/location/', 'location')

if __name__ == "__main__":
    app.run(debug=DEBUG)
