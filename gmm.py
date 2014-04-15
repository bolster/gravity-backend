import requests
import struct

from decimal import Decimal, getcontext, ROUND_DOWN


class GMMDataSource(object):
    URI_PREFIX = "http://gravityapp.s3.amazonaws.com/ga/"
    # BIG endian int32 as specified in
    # http://ddfe.curtin.edu.au/gravitymodels/GGMplus/GGMplus_readme.dat
    DATA_FORMAT = ">i"

    ROW_WIDTH = 2500
    COLUMN_HEIGHT = 2500

    def pick_file(self, lat, lon):
        """
        The integer meridian and parallel located closest to the
        South-Westernmost data point of each 5 deg x 5 deg determines the
        filename, and the functional determines the suffix. For instance the
        file N50E005.ga contains gravity accelerations over the area 50.001 to
        54.999 degree geodetic latitude, and 5.001 to 9.999 degree geodetic
        longitude.
        """
        if lat < 0:
            latitude_direction = "S"
            lat = -lat
            lat_ref = (int(lat) / 5 + 1) * 5
        else:
            latitude_direction = "N"
            lat_ref = (int(lat) / 5) * 5
        if lon < 0:
            longitude_direction = "W"
            lon = -lon
            lon_ref = (int(lon) / 5 + 1) * 5
        else:
            longitude_direction = "E"
            lon_ref = (int(lon) / 5) * 5

        return "%s%02d%s%03d.ga" % (latitude_direction, lat_ref,
                                    longitude_direction, lon_ref)

    def get_data_offset(self, lat, lon):
        """
        Records proceed along meridians from South to North and columns proceed
        from West to East. The first record is the South-West corner (50.001
        deg latitude, 5.001 deg longitude in the example), and the last record
        is the North-East corner (54.999 deg latitude, 9.999 deg longitude).
        No-data values (see Table) flag offshore areas (i.e. about 10 km or
        further away from the nearest land point).
        """
        c = getcontext()
        FIVE = Decimal('5.0')

        lat_effective = c.divmod(lat, FIVE)[1].quantize(
            Decimal('.001'), rounding=ROUND_DOWN)
        lon_effective = c.divmod(lon, FIVE)[1].quantize(
            Decimal('.001'), rounding=ROUND_DOWN)

        # GET LATITUDE OFFSET
        if lat_effective < 0:
            lat_effective = FIVE + lat_effective
        y_offset = int(lat_effective / FIVE * self.COLUMN_HEIGHT)
        print "Picked row %d" % y_offset

        # GET LONGITUDE OFFSET
        if lon_effective < 0:
            lon_effective = FIVE + lon_effective
        x_offset = int(lon_effective / FIVE * self.ROW_WIDTH)
        print "Picked column %d" % x_offset

        record_offset = y_offset + x_offset * self.COLUMN_HEIGHT

        print "Record offset: %d (%d)" % (record_offset, record_offset * 4)

        return record_offset * 4

    def get_gravitational_acceleration_at_point(self, lat, lon):
        try:
            filename = self.pick_file(lat, lon)
            url = "%s%s" % (self.URI_PREFIX, filename)
            offset = self.get_data_offset(lat, lon)
            r = requests.get(
                url, headers={'Range': 'bytes=%d-%d' % (offset, offset + 3)})
            val = struct.unpack(self.DATA_FORMAT, r.content)[0]
            if val == -2 ** 31:
                raise ValueError("No data available.")
            return val * .1
        except Exception, e:
            print e
            return None
