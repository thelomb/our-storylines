from application import images
from application.models import Story, Media, GeoPoint, Itinerary
from application.model_enums import TravelType
from datetime import timedelta
from application.location_service import Geolocation


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
                      author,
                      files):
        print('from web form')
        instance = cls()
        instance.date_for = date_for
        instance.title = title
        instance.content = content
        instance.stay_place = stay_place
        instance.start_place = start_place
        instance.end_place = end_place
        instance.odometer_at = odometer_at
        instance.travel_type = TravelType[travel_type]
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
                     media=instance.media,
                     stay=instance.stay,
                     itinerary=instance.itinerary)
        print('end create')

    def update(self,
               date_for,
               title,
               content,
               start_place,
               end_place,
               stay_place,
               odometer_at,
               travel_type,
               author,
               files
               ):
        self.media = self.story.media
        self.title = title
        self.content = content
        self.start_place = start_place
        self.end_place = end_place
        self.stay_place = stay_place
        self.odometer_at = odometer_at
        self.travel_type = TravelType[travel_type]
        self.author = author
        self.files = files
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
                          stay=self.stay,
                          itinerary=self.itinerary)

    @classmethod
    def get_by_date(cls, date_for):
        story = Story.query.filter_by(date_for=date_for).first()
        fullstory = cls(story)
        return fullstory

    @classmethod
    def get_by_date_web(cls, date_for):
        fullstory = cls.get_by_date(date_for)
        if fullstory.story is None:
            return None
        fullstory.date_for = fullstory.story.date_for
        fullstory.title = fullstory.story.title
        fullstory.content = fullstory.story.content
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
        prev_story = cls.get_by_date(date_for - timedelta(days=1))
        if prev_story.story is None:
            fullstory.prev_date = None
        else:
            fullstory.prev_date = prev_story.story.date_for
            prev_distance = 0
            if prev_story.story.itinerary:
                prev_distance = prev_story.story.itinerary.odomter_at
            if fullstory.story.itinerary:
                fullstory.distance = fullstory.odometer_at -\
                    prev_distance
        next_story = cls.get_by_date(date_for + timedelta(days=1))
        if next_story.story is None:
            fullstory.next_date = None
        else:
            fullstory.next_date = next_story.story.date_for
        return fullstory

    def process_media_files(self):
        photo = []
        if self.files:
            for image_info in self.files:
                    filename = images.save(image_info)
                    url = images.url(filename)
                    image = Media(name=filename,
                                  filename=filename,
                                  url=url,
                                  type='Image')
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
                     'category': 'hotel',
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
        return geopoints
