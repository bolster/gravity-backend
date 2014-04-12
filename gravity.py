import os
import wolframalpha

from flask import Flask
from restless.exceptions import NotFound
from restless.fl import FlaskResource

app = Flask(__name__)

APP_ID = os.environ['APP_ID']


class LocationResource(FlaskResource):

    def list(self):
        query = dict(self.request.args).get('q', None)

        if query is None:
            raise NotFound('Location not found or not specified.')

        location = query[0]
        client = wolframalpha.Client(APP_ID)
        result = client.query('gravitation acceleration {}'.format(location))
        pod = [
            pod.text for pod in result.pods
            if pod.text and pod.text.startswith('total field')
        ][0].split('\n')[0]
        acceleration = float(pod.split('|')[1].strip().split(' ')[0])

        return [{
            'location': location,
            'acceleration': acceleration,
        }]

    def serialize(self, method, endpoint, data):
        return self.serialize_detail(data)


LocationResource.add_url_rules(app, '/api/v1/location/', 'location')

if __name__ == "__main__":
    app.run(debug='DEBUG' in os.environ and os.environ['DEBUG'] == 'True')
