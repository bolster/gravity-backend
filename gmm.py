from decimal import Decimal, getcontext, ROUND_DOWN
import requests
import struct


class GMMDataSource(object):
    URI_PREFIX = "http://gravityapp.s3.amazonaws.com/ga/"
    # BIG endian int32 as specified in
    # http://ddfe.curtin.edu.au/gravitymodels/GGMplus/GGMplus_readme.dat
    DATA_FORMAT = ">i"

    ROW_LENGTH = 1000
    COLUMN_HEIGHT = 1000

    def pick_file(self, lat, lon):
        if lat < 0:
            latitude_direction = "S"
            lat = -lat
        else:
            latitude_direction = "N"
        if lon < 0:
            longitude_direction = "W"
            lon = -lon
        else:
            longitude_direction = "E"
        lat_ref = (int(lat) / 5) * 5
        lon_ref = (int(lon) / 5) * 5
        return "%s%02d%s%03d.ga" % (latitude_direction, lat_ref,
                                    longitude_direction, lon_ref)

    def get_data_offset(self, lat, lon):
        c = getcontext()
        lat_effective = c.divmod(c.abs(lat), Decimal('5.0'))[1].quantize(
            Decimal('.001'), rounding=ROUND_DOWN)
        lon_effective = c.divmod(c.abs(lon), Decimal('5.0'))[1].quantize(
            Decimal('.001'), rounding=ROUND_DOWN)
        lon_offset = int(lon_effective / Decimal('5.0') * 1000)
        lat_offset = int(lat_effective / Decimal('5.0') * 1000)
        record_offset = lat_offset * (self.ROW_LENGTH) * 4 + lon_offset * 4
        return record_offset

    def get_gravitational_acceleration_at_point(self, lat, lon):
        filename = self.pick_file(lat, lon)
        url = "%s%s" % (self.URI_PREFIX, filename)
        offset = self.get_data_offset(lat, lon)
        r = requests.get(
            url, headers={'Range': 'bytes=%d-%d' % (offset, offset + 3)})
        return struct.unpack(self.DATA_FORMAT, r.content)[0] * 0.1
