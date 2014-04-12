#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wolframalpha

from clint.arguments import Args
from clint.textui import puts, colored, indent

args = Args()

location = ' '.join(args.all)

if location is None:
    puts(colored.red('You must provide a location.'))
else:
    puts(colored.yellow('Querying for gravity data for: ')
         + colored.green(location))

    client = wolframalpha.Client('K885R7-9J7K9H6LP8')
    result = client.query('gravitational acceleration {}'.format(location))
    pod = [
        pod.text for pod in result.pods
        if pod.text and pod.text.startswith('total field')
    ][0].split('\n')[0]
    acceleration = float(pod.split('|')[1].strip().split(' ')[0])
    with indent(4, quote='>>>'):
        puts(colored.red('{} m/s^2'.format(acceleration)))
