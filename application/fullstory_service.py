from flask import current_app
from application import images
from application.models import Story, Media, GeoPoint, Itinerary
from googlemaps import Client
from application.model_enums import TravelType


class Fullstory2(object):

    def __init__(self, story=None):
        self.story = story
        print('init')

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
        story = Story.query.filter_by(date_for=date_for).first_or_404()
        fullstory = cls(story)
        return fullstory

    @classmethod
    def get_by_date_web(cls, date_for):
        fullstory = cls.get_by_date(date_for)
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
        geolocation = Client(current_app.config['GOOGLEMAPS_KEY'])
        geocode_result = geolocation.geocode(self.stay_place)
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
        fmt_addr = geocode_result[0]['formatted_address']
        self.stay = GeoPoint(place=self.stay_place,
                             latitude=lat,
                             longitude=lng,
                             formatted_address=fmt_addr)

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


class Fullstory(object):

    def __init__(self,
                 date_for,
                 title,
                 content,
                 files=None,
                 start=None,
                 end=None,
                 stay_place=None,
                 odometer_at=None,
                 travel_type=None,
                 author=None,
                 story=None,
                 media=None,
                 stay=None,
                 itinerary=None):
        self.date_for = date_for
        self.title = title
        self.content = content
        self.start = start
        self.end = end
        self.stay_place = stay_place
        self.odometer_at = odometer_at
        self.travel_type = (travel_type if travel_type else TravelType.NONE)
        self.author = author
        self.files = files
        self.story = story
        self.media = []
        self.stay = stay
        self.itinerary = itinerary
        if self.files:
            self.process_media_files()
        if self.stay_place:
            self.process_stay()
        if self.start and self.end:
            self.process_itinerary()
        print('init fullstory')

    def store(self):
        Story.create(date_for=self.date_for,
                     title=self.title,
                     content=self.content,
                     user_id=self.author.id,
                     media=self.media,
                     stay=self.stay,
                     itinerary=self.itinerary)
        print('story created!')

    def update(self,
               date_for,
               title,
               content,
               start,
               end,
               stay_place,
               odometer_at,
               travel_type,
               author,
               files):
        self.media = self.story.media
        self.title = title
        self.content = content
        self.start = start
        self.end = end
        self.stay_place = stay_place
        self.odometer_at = odometer_at
        self.travel_type = TravelType[travel_type]
        self.author = author
        self.files = files
        if self.files:
            self.process_media_files()
        if self.stay_place:
            self.process_stay()
        if self.start and self.end:
            self.process_itinerary()
        self.story.update(date_for=self.date_for,
                          title=self.title,
                          content=self.content,
                          user_id=self.author.id,
                          stay=self.stay,
                          itinerary=self.itinerary)

    @classmethod
    def get_by_date(cls, date_for):
        story = Story.query.filter_by(date_for=date_for).first_or_404()
        fullstory = cls(date_for=story.date_for,
                        title=story.title,
                        content=story.content,
                        story=story,
                        stay=story.stay,
                        itinerary=story.itinerary,
                        start=story.itinerary.start.place,
                        end=story.itinerary.end.place,
                        odometer_at=story.itinerary.odometer_at,
                        travel_type=story.itinerary.travel_type,
                        stay_place=story.stay.place)
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

    def process_stay(self):
        if self.story:
            if self.story.stay:
                if self.stay_place == self.story.stay.place:
                    return
                self.story.stay.delete()
        geolocation = Client(current_app.config['GOOGLEMAPS_KEY'])
        geocode_result = geolocation.geocode(self.stay_place)
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
        fmt_addr = geocode_result[0]['formatted_address']
        self.stay = GeoPoint(place=self.stay_place,
                             latitude=lat,
                             longitude=lng,
                             formatted_address=fmt_addr)

    def process_itinerary(self):
        if self.story:
            if self.story.itinerary:
                print('deleting itinerary', self.story.itinerary.id)
                self.story.itinerary.delete()
        location = Geolocation(self.start)
        start = GeoPoint(place=self.start,
                         latitude=location.lat,
                         longitude=location.lng,
                         formatted_address=location.fmt_addr)
        location = Geolocation(self.end)
        end = GeoPoint(place=self.end,
                       latitude=location.lat,
                       longitude=location.lng,
                       formatted_address=location.fmt_addr)
        self.itinerary = Itinerary(odometer_at=self.odometer_at,
                                   travel_type=self.travel_type,
                                   start=start,
                                   end=end)


class Geolocation():
    def __init__(self, place):
        geolocation = Client(current_app.config['GOOGLEMAPS_KEY'])
        geocode_result = geolocation.geocode(place)
        self.lat = geocode_result[0]['geometry']['location']['lat']
        self.lng = geocode_result[0]['geometry']['location']['lng']
        self.fmt_addr = geocode_result[0]['formatted_address']
