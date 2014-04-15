import wolframalpha

from datetime import datetime
from urllib import urlencode


class WolframAlphaDataSource(object):

    def __init__(self, app_id):
        self.app_id = app_id
        self.query = ''

    def get_gravitational_acceleration_at_point(self, lat, lon):
        client = wolframalpha.Client(self.app_id)
        self.query = 'gravitational acceleration {} {}'.format(lat, lon)
        result = client.query(self.query)

        pod = [
            pod.text for pod in result.pods
            if pod.text and pod.text.startswith('total field')
        ][0].split('\n')[0]
        acceleration = float(pod.split('|')[1].strip().split(' ')[0])

        return acceleration, self.source

    @property
    def source(self):
        return {
            'Author/Site': 'Wolfram|Alpha',
            'Publisher': 'Wolfram Alpha LLC',
            'URL': 'http://api.wolframalpha.com/v2/query?{}'.format(
                urlencode({'input': self.query})),
            'Date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
        }
