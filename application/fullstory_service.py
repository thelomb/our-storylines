from application import images, db
from application.models import (Story,
                                Media,
                                GeoPoint,
                                Itinerary,
                                Storyline,
                                Comment)
from application.model_enums import TravelType, StayType, ImageFeature
from application.location_service import Geolocation
from application.imagery import WebImage
from PIL import Image


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
                      files,
                      storyline,
                      stay_description):
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
        instance.storyline_id = storyline.id
        instance.stay_description = stay_description
        instance.media = []
        if instance.stay_place:
            instance.create_stay()
        if instance.start_place and instance.end_place:
            instance.create_itinerary()
        else:
            instance.itinerary = None
        if instance.files:
            instance.process_media_files()
        Story.create(commit=False,
                     date_for=instance.date_for,
                     title=instance.title,
                     content=instance.content,
                     user_id=instance.author.id,
                     stay_type=instance.stay_type,
                     media=instance.media,
                     stay=instance.stay,
                     itinerary=instance.itinerary,
                     storyline_id=instance.storyline_id,
                     stay_description=instance.stay_description)
        db.session.commit()

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
               image_addons,
               stay_description):
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
        self.image_addons = image_addons
        self.stay_description = stay_description
        if self.files:
            self.process_media_files()
        if self.stay_place:
            self.process_stay()
        if self.start_place and self.end_place:
            self.process_itinerary()
        else:
            self.itinerary = None
        if self.media:
            self.process_media_addons()
        self.story.update(commit=False,
                          date_for=self.date_for,
                          title=self.title,
                          content=self.content,
                          user_id=self.author.id,
                          stay_type=self.stay_type,
                          stay=self.stay,
                          itinerary=self.itinerary,
                          stay_description=self.stay_description)
        db.session.commit()

    @classmethod
    def get_by_date(cls, date_for, storyline_slug):
        storyline = Storyline.query.filter_by(slug=storyline_slug).first()
        if storyline is None:
            return None
        stories = storyline.stories
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
        filtered_stories = {}
        cumulative_distance = 0
        cumulate = False
        for i, story in enumerate(stories):

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

            if story.date_for == date_for:
                filtered_stories['current'] = story
                if i > 0:
                    filtered_stories['previous'] = stories[i - 1]

                try:
                    filtered_stories['next'] = stories[i + 1]
                except IndexError:
                    pass

                break

        filtered_stories['nb_stories'] = i + 1
        filtered_stories['cumulative_distance'] = cumulative_distance
        return filtered_stories

    @classmethod
    def get_by_date_web(cls, date_for, storyline):
        fullstory = cls.get_by_date(date_for, storyline)
        if fullstory is None:
            return None
        fullstory.date_for = fullstory.story.date_for
        fullstory.title = fullstory.story.title
        fullstory.content = fullstory.story.content
        fullstory.html_content = fullstory.story.html_content
        fullstory.stay_type = fullstory.story.stay_type.name
        fullstory.stay_type_label = fullstory.story.stay_type.value
        fullstory.stay_description = fullstory.story.stay_description
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

    def process_media_addons(self):
        if self.media:
            for medium in self.media:
                comment = self.image_addons.get('comments').\
                    get(medium.filename, None)
                feature = self.image_addons.get('features').\
                    get(medium.filename, None)
                medium.comment = comment
                medium.feature = ImageFeature[feature]
                medium.save(commit=False)

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
                self.story.stay.delete(commit=False)
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
                self.story.itinerary.delete(commit=False)
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
                                      'image': medium.url,
                                      'comment': medium.comment
                                      })

        return geopoints

    def add_comment(self, comment, author):
        if comment and self.story:
            new_comment = Comment(content=comment,
                                  author=author)
            new_comment.save(commit=False)
            self.story.comments.append(new_comment)
            self.story.save(commit=False)
            db.session.commit()

    def featured_image(self):
        image = None
        if self.media:
            for medium in self.media:
                if medium.feature == ImageFeature.FEATURED:
                    return medium
        return image
