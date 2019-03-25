from flask import current_app
from application import images
from application.models import Story, Media, GeoPoint
from googlemaps import Client


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
                 stay=None):
        self.date_for = date_for
        self.title = title
        self.content = content
        self.start = start
        self.end = end
        self.stay_place = stay_place
        self.odometer_at = odometer_at
        self.travel_type = travel_type
        self.author = author
        self.files = files
        self.story = story
        self.media = []
        self.stay = stay
        if self.files:
            self.process_media_files()
        if self.stay_place:
            self.process_stay()
        print('init fullstory')

    def store(self):
        Story.create(date_for=self.date_for,
                     title=self.title,
                     content=self.content,
                     user_id=self.author.id,
                     media=self.media,
                     stay=self.stay)
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
        self.travel_type = travel_type
        self.author = author
        self.files = files
        if self.files:
            self.process_media_files()
        if self.stay_place:
            self.process_stay()
        self.story.update(date_for=self.date_for,
                          title=self.title,
                          content=self.content,
                          user_id=self.author.id,
                          stay=self.stay)

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

    @classmethod
    def get_by_date(cls, date_for):
        story = Story.query.filter_by(date_for=date_for).first_or_404()
        fullstory = cls(date_for=story.date_for,
                        title=story.title,
                        content=story.content,
                        story=story,
                        stay=story.stay)
        return fullstory
