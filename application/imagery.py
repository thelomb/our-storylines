from PIL import Image, ExifTags, ImageOps
from flask import current_app

class WebImage(object):
    def __init__(self, image):
        self._image = image
        self.exif = None
        self.latitude = None
        self.longitude = None
        self.exif_width = None
        self.exif_height = None
        self.gps = None
        self._get_exif()
        self._to_latitude()
        self._to_longitude()
        self._to_image_ratio()

    def save(self, filename):
        self._image.save(filename)

    def close(self):
        self._image.close()

    def _get_exif(self):
        try:
            current_app.logger.error('exif present in get exif method')
            self.exif = self._image._getexif()
            self._GPS_on_exif()
            current_app.logger.error('exif present in get exif method',
                                     self.exif)
        except (AttributeError, KeyError, IndexError):
            current_app.logger.error('failed to get exif')

    def fix_orientation(self):
        if self.exif:
            for tag, value in self.exif.items():
                if ExifTags.TAGS.get(tag, tag) == 'Orientation':
                    if value == 3:
                        self._image = self._image.rotate(180, expand=True)
                    elif value == 6:
                        self._image = self._image.rotate(270, expand=True)
                        self.exif_width, self.exif_height =\
                            self.exif_height, self.exif_width
                    elif value == 8:
                        self._image = self._image.rotate(90, expand=True)
                        self.exif_width, self.exif_height =\
                            self.exif_height, self.exif_width

    def _GPS_on_exif(self):
        self.gps = {}
        if self.exif:

            for tag, value in self.exif.items():
                if ExifTags.TAGS.get(tag, tag) == 'GPSInfo':
                    for k, v in value.items():
                        self.gps[ExifTags.GPSTAGS.get(k, k)] = v

    def _to_latitude(self):
        if self.gps:
            if self.gps.get('GPSLatitude') and self.gps.get('GPSLatitudeRef'):
                multiplier = 1
                if not self.gps.get('GPSLatitudeRef') == 'N':
                    multiplier = -1
                self.latitude = self._convert_to_degrees(
                    self.gps.get('GPSLatitude')) * multiplier

    def _to_longitude(self):
        if self.gps:
            if self.gps.get('GPSLongitude') and\
                    self.gps.get('GPSLongitudeRef'):
                multiplier = 1
                if not self.gps.get('GPSLongitudeRef') == 'E':
                    multiplier = -1
                self.longitude = self._convert_to_degrees(
                    self.gps.get('GPSLongitude')) * multiplier

    def _to_image_ratio(self):
        if self.exif:
            for tag, value in self.exif.items():
                if ExifTags.TAGS.get(tag, tag) == 'ExifImageHeight':
                    self.exif_height = value
                if ExifTags.TAGS.get(tag, tag) == 'ExifImageWidth':
                    self.exif_width = value

    @staticmethod
    def _convert_to_degrees(value):
        """
        Helper function to convert the GPS coordinates stored
        in the EXIF to degress in float format
        :param value:
        :type value: exifread.utils.Ratio
        :rtype: float
        """
        try:
            d = float(value[0][0]) / float(value[0][1])
            m = float(value[1][0]) / float(value[1][1])
            s = float(value[2][0]) / float(value[2][1])
            return d + (m / 60.0) + (s / 3600.0)
        except ValueError:
            return 0

    def resize_image(self, width=1024, height=700):
        size = (width, height)
        image = self._image
        image.thumbnail(size, Image.ANTIALIAS)
        resized = Image.new('RGBA', size, (255, 255, 255, 0))
        resized.paste(
            image, (int((size[0] - image.size[0]) / 2),
                    int((size[1] - image.size[1]) / 2))
        )
        return resized

# def resize_image(filepath, i):
#     size = (1024, 700)
#     image = Image.open(filepath)
#     image.thumbnail(size, Image.ANTIALIAS)
#     background = Image.new('RGBA', size, (255, 255, 255, 0))
#     background.paste(
#         image, (int((size[0] - image.size[0]) / 2),
#                 int((size[1] - image.size[1]) / 2))
#     )
#     background.save("squared"+str(i)+".png")

    def square_thumbnail(self):
        thumb = ImageOps.fit(self._image, (256, 256), Image.ANTIALIAS)
        return thumb



# gps GPSLatitudeRef N
# gps GPSLatitude ((46, 1), (10, 1), (1629, 100))
# gps GPSLongitudeRef E
# gps GPSLongitude ((9, 1), (24, 1), (259, 100))
# gps GPSAltitudeRef b'\x00'
# gps GPSAltitude (49776, 233)
# gps GPSTimeStamp ((12, 1), (5, 1), (2999, 100))
# gps GPSSpeedRef K
# gps GPSSpeed (583, 14617)
# gps GPSImgDirectionRef T
# gps GPSImgDirection (27659, 108)
# gps GPSDestBearingRef T
# gps GPSDestBearing (45585, 599)
# gps GPSDateStamp 2017:08:13
# gps GPSHPositioningError (8, 1)
