from application import images
from application.models import Story, Media, GeoPoint, Itinerary
from application.model_enums import TravelType, StayType
from datetime import timedelta
from application.location_service import Geolocation
from PIL import Image, ExifTags


class Fullstory2(object):

    def __init__(self, story=None):
        self.story = story

    @classmethod
    def from_web_form(cls,
                      date_for,
                      title,
                      content,
                      start_place,
                      end_place,
                      stay_place,
                      odometer_at,
                      travel_type,
                      stay_type,
                      author,
                      files):
        instance = cls()
        instance.date_for = date_for
        instance.title = title
        instance.content = content
        instance.stay_place = stay_place
        instance.start_place = start_place
        instance.end_place = end_place
        instance.odometer_at = odometer_at
        instance.travel_type = TravelType[travel_type]
        instance.stay_type = StayType[stay_type]
        instance.author = author
        instance.files = files
        instance.media = []
        if instance.stay_place:
            instance.create_stay()
        if instance.start_place and instance.end_place:
            instance.create_itinerary()
        else:
            instance.itinerary = None
        if instance.files:
            instance.process_media_files()
        Story.create(date_for=instance.date_for,
                     title=instance.title,
                     content=instance.content,
                     user_id=instance.author.id,
                     stay_type=instance.stay_type,
                     media=instance.media,
                     stay=instance.stay,
                     itinerary=instance.itinerary)

    def update(self,
               date_for,
               title,
               content,
               start_place,
               end_place,
               stay_place,
               odometer_at,
               travel_type,
               stay_type,
               author,
               files,
               image_comments
               ):
        self.media = self.story.media
        self.title = title
        self.content = content
        self.start_place = start_place
        self.end_place = end_place
        self.stay_place = stay_place
        self.odometer_at = odometer_at
        self.travel_type = TravelType[travel_type]
        self.stay_type = StayType[stay_type]
        self.author = author
        self.files = files
        self.image_comments = image_comments
        if self.files:
            self.process_media_files()
        if self.stay_place:
            self.process_stay()
        if self.start_place and self.end_place:
            self.process_itinerary()
        else:
            self.itinerary = None
        self.story.update(date_for=self.date_for,
                          title=self.title,
                          content=self.content,
                          user_id=self.author.id,
                          stay_type=self.stay_type,
                          stay=self.stay,
                          itinerary=self.itinerary)

    @classmethod
    def get_by_date(cls, date_for):
        stories = Story.query.filter(Story.date_for <= date_for +
                                     timedelta(days=1)).all()
        filtered_stories = cls._current_prev_next_stories(stories=stories,
                                                          date_for=date_for)
        fullstory = cls(filtered_stories.get('current', None))
        fullstory.nb_stories = filtered_stories.get('nb_stories')
        fullstory.prev_date_story = filtered_stories.get('previous', None)
        fullstory.next_date_story = filtered_stories.get('next', None)
        fullstory.cumulative_distance = filtered_stories.\
            get('cumulative_distance', None)
        return fullstory

    @staticmethod
    def _current_prev_next_stories(stories, date_for):
        next = False
        filtered_stories = {}
        cumulative_distance = 0
        cumulate = False
        for i, story in enumerate(stories):
            if story.date_for == date_for + timedelta(days=1):
                filtered_stories['next'] = story
                next = True
            else:
                if story.date_for == date_for:
                    filtered_stories['current'] = story

                if story.date_for == date_for - timedelta(days=1):
                    filtered_stories['previous'] = story

                if story.itinerary:
                    if story.itinerary.travel_type == TravelType.FLIGHT:
                        cumulate = True

                if not cumulate and story.itinerary:
                    cumulative_distance = max(cumulative_distance,
                                              story.itinerary.odometer_at)
                elif story.itinerary:
                        if story.itinerary.odometer_at > 0:
                            cumulative_distance = cumulative_distance +\
                                story.itinerary.odometer_at
                            cumulate = False

        filtered_stories['nb_stories'] = len(stories) - next
        filtered_stories['cumulative_distance'] = cumulative_distance
        return filtered_stories

    @classmethod
    def get_by_date_web(cls, date_for):
        fullstory = cls.get_by_date(date_for)
        if fullstory.story is None:
            return None
        fullstory.date_for = fullstory.story.date_for
        fullstory.title = fullstory.story.title
        fullstory.content = fullstory.story.content
        fullstory.html_content = fullstory.story.html_content
        fullstory.stay_type = fullstory.story.stay_type.name
        fullstory.stay_type_label = fullstory.story.stay_type.value
        # if fullstory.story.stay:
        fullstory.stay_place = (fullstory.story.stay.place
                                if fullstory.story.stay else None)
        fullstory.start_place = (fullstory.story.itinerary.start.place
                                 if fullstory.story.itinerary else None)
        fullstory.end_place = (fullstory.story.itinerary.end.place
                               if fullstory.story.itinerary else None)
        fullstory.odometer_at = (fullstory.story.itinerary.odometer_at
                                 if fullstory.story.itinerary else None)
        fullstory.travel_type = (fullstory.story.itinerary.travel_type.name
                                 if fullstory.story.itinerary else None)
        fullstory.media = (fullstory.story.media
                           if fullstory.story.media else None)
        # prev_story = cls.get_by_date(date_for - timedelta(days=1))
        # odo_read = story.itinerary.odometer_at\
        #     if story.itinerary else 0
        # prev_odo_read = stories[min(0, i - 1)].itinerary.odometer_at\
        #     if stories[min(0, i - 1)].itinerary else 0
        # distance = odo_read - prev_odo_read

        if fullstory.prev_date_story:
            fullstory.prev_date = fullstory.prev_date_story.date_for
            prev_distance = 0
            if fullstory.prev_date_story.itinerary:
                if fullstory.prev_date_story.itinerary.travel_type ==\
                        TravelType['CAR']:
                    prev_distance = fullstory.prev_date_story.\
                        itinerary.odometer_at
            if fullstory.story.itinerary:
                if fullstory.story.itinerary.travel_type == TravelType['CAR']:
                    fullstory.distance =\
                        fullstory.story.itinerary.odometer_at -\
                        prev_distance
        else:
            fullstory.prev_date = None
        if fullstory.next_date_story:
            fullstory.next_date = fullstory.next_date_story.date_for
        else:
            fullstory.next_date = None
        return fullstory

    def process_media_files(self):
        photo = []
        if self.files:
            for image_info in self.files:
                new_image = True
                if self.media:
                    for medium in self.media:
                        if medium.request_file_name == image_info.filename:
                            new_image = False
                            break
                if new_image:
                    filename = images.save(image_info)
                    path = images.path(filename)
                    url = images.url(filename)
                    web_image = WebImage(Image.open(path))
                    web_image.fix_orientation()
                    web_image.save(path)
                    geo_point = GeoPoint(place='tdb',
                                         latitude=web_image.latitude,
                                         longitude=web_image.longitude,
                                         formatted_address='')
                    image = Media(name=filename,
                                  filename=filename,
                                  url=url,
                                  type='Image',
                                  request_file_name=image_info.filename,
                                  location=geo_point,
                                  exif_width=web_image.exif_width,
                                  exif_height=web_image.exif_height)
                    web_image.close()
                    photo.append(image)
            if self.media:
                self.media.extend(photo)
            else:
                self.media = photo

    def create_stay(self):
        location = Geolocation(self.stay_place)
        self.stay = GeoPoint(place=self.stay_place,
                             latitude=location.lat,
                             longitude=location.lng,
                             formatted_address=location.fmt_addr)

    def process_stay(self):
        if self.story:
            if self.story.stay:
                self.story.stay.delete()
        self.create_stay()

    def create_itinerary(self):
        location = Geolocation(self.start_place)
        start = GeoPoint(place=self.start_place,
                         latitude=location.lat,
                         longitude=location.lng,
                         formatted_address=location.fmt_addr)
        location = Geolocation(self.end_place)
        end = GeoPoint(place=self.end_place,
                       latitude=location.lat,
                       longitude=location.lng,
                       formatted_address=location.fmt_addr)
        self.itinerary = Itinerary(odometer_at=self.odometer_at,
                                   travel_type=self.travel_type,
                                   start=start,
                                   end=end)

    def process_itinerary(self):
        if self.story:
            if self.story.itinerary:
                self.story.itinerary.delete()
        self.create_itinerary()

    def get_geo_points(self):
        geopoints = []
        if self.story.stay:
            point = {'place': self.story.stay.place,
                     'lat': self.story.stay.latitude,
                     'lng': self.story.stay.longitude,
                     'fmt_addr': self.story.stay.formatted_address,
                     'category': self.story.stay_type.name,
                     'type': 'stay'
                     }
            geopoints.append(point)
        if self.story.itinerary:
            start = {'place': self.story.itinerary.start.place,
                     'lat': self.story.itinerary.start.latitude,
                     'lng': self.story.itinerary.start.longitude,
                     'fmt_addr': self.story.itinerary.start.formatted_address,
                     'category': 'start',
                     'type': 'start'
                     }
            end = {'place': self.story.itinerary.end.place,
                   'lat': self.story.itinerary.end.latitude,
                   'lng': self.story.itinerary.end.longitude,
                   'fmt_addr': self.story.itinerary.end.formatted_address,
                   'category': 'end',
                   'type': 'end'
                   }
            geopoints.append(start)
            geopoints.append(end)
        location = 0
        if self.story.media:
            for medium in self.story.media:
                if medium.location:
                    location += 1
                    geopoints.append({'place': 'location #' + str(location),
                                      'lat': medium.location.latitude,
                                      'lng': medium.location.longitude,
                                      'fmt_addr':
                                      medium.location.formatted_address,
                                      'category': 'picture',
                                      'type': 'picture',
                                      'image': medium.url
                                      })

        return geopoints


class WebImage(object):
    def __init__(self, image):
        self._image = image
        self.exif = None
        self.latitude = None
        self.longitude = None
        self.exif_width = None
        self.exif_height = None
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
            self.exif = self._image._getexif()
            self._GPS_on_exif()
        except (AttributeError, KeyError, IndexError):
            print('failed to get exif')

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
