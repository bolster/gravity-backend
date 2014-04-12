import os
import wolframalpha

from flask import Flask
from pymongo import MongoClient, GEOSPHERE
from restless.fl import FlaskResource

app = Flask(__name__)

APP_ID = os.getenv('APP_ID')

client = MongoClient(
    os.getenv('MONGOHQ_URL', 'mongodb://localhost:27017/gravity')
)
db = getattr(client, os.getenv('DATABASE_NAME', 'gravity'))
db.locations.ensure_index([('location', GEOSPHERE)])


class LocationResource(FlaskResource):

    def list(self):
        query = self.request.args.to_dict()

        location = {
            'type': 'Point',
            'coordinates': [float(query['long']), float(query['lat'])],
        }

        cached = db.locations.find({
            "location": {
                "$nearSphere": location,
                '$maxDistance': 500,
            }}).limit(1)

        if cached.count() > 0:
            location = cached[0]
            return {
                'acceleration': location['acceleration'],
                'location': location['location'],
            }

        client = wolframalpha.Client(APP_ID)
        result = client.query(
            'gravitational acceleration {} {}'.format(
                location['coordinates'][0],
                location['coordinates'][1]))
        pod = [
            pod.text for pod in result.pods
            if pod.text and pod.text.startswith('total field')
        ][0].split('\n')[0]
        acceleration = float(pod.split('|')[1].strip().split(' ')[0])

        result = {
            'acceleration': acceleration,
            'location': location,
        }

        db.locations.insert(result)

        return result

    def serialize(self, method, endpoint, data):
        return self.serialize_detail(data)


LocationResource.add_url_rules(app, '/api/v1/location/', 'location')

if __name__ == "__main__":
    app.run(debug='DEBUG' in os.environ and os.environ['DEBUG'] == 'True')
