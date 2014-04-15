import os
import wolframalpha

from datetime import datetime
from urllib import urlencode

from pymongo import MongoClient, GEOSPHERE


class WolframAlphaDataSource(object):

    def __init__(self, app_id):
        self.app_id = app_id
        self.query = ''

    def get_gravitational_acceleration_at_point(self, location):
        result = self.get_cached_acceleration(location) \
            or self.query_wolfram(location)

        return result

    def get_source(self):
        return {
            'Author/Site': 'Wolfram|Alpha',
            'Publisher': 'Wolfram Alpha LLC',
            'URL': 'http://api.wolframalpha.com/v2/query?{}'.format(
                urlencode({'input': self.query})),
            'Date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
        }

    def get_cached_acceleration(self, location):
        client = MongoClient(
            os.getenv('MONGOHQ_URL', 'mongodb://localhost:27017/gravity')
        )
        self.db = getattr(client, os.getenv('DATABASE_NAME', 'gravity'))
        self.db.locations.ensure_index([('location', GEOSPHERE)])

        location['coordinates'] = map(float, location['coordinates'])

        try:
            cached = self.db.locations.find({
                "location": {
                    "$nearSphere": location,
                    '$maxDistance': 500,
                }}).limit(1)
            result = cached[0]
        except:
            result = None
        finally:
            return result

    def query_wolfram(self, location):
        lat = location['coordinates'][1]
        lon = location['coordinates'][0]

        client = wolframalpha.Client(self.app_id)
        self.query = 'gravitational acceleration {} {}'.format(lat, lon)
        response = client.query(self.query)

        pod = [
            pod.text for pod in response.pods
            if pod.text and pod.text.startswith('total field')
        ][0].split('\n')[0]
        acceleration = float(pod.split('|')[1].strip().split(' ')[0])

        result = {
            'acceleration': acceleration,
            'location': location,
            'source': self.get_source()
        }

        try:
            self.db.locations.insert(result)
        except:
            pass

        return result
