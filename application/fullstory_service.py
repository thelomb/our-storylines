from application import images
from application.models import Story, Media


class Fullstory():

    def __init__(self,
                 date_for,
                 title,
                 content,
                 files=None,
                 start=None,
                 end=None,
                 stay=None,
                 odometer_at=None,
                 travel_type=None,
                 author=None,
                 story=None,
                 media=None):
        self.date_for = date_for
        self.title = title
        self.content = content
        self.start = start
        self.end = end
        self.stay = stay
        self.odometer_at = odometer_at
        self.travel_type = travel_type
        self.author = author
        self.files = files
        self.story = story
        self.media = []
        if self.files:
            self.process_media_files()

    def store(self):
        Story.create(date_for=self.date_for,
                     title=self.title,
                     content=self.content,
                     user_id=self.author.id,
                     media=self.media)
        print('story created!')

    def update(self, date_for, title, content, start, end, stay,
               odometer_at, travel_type, author, files):
        self.media = self.story.media
        self.title = title
        self.content = content
        self.start = start
        self.end = end
        self.stay = stay
        self.odometer_at = odometer_at
        self.travel_type = travel_type
        self.author = author
        self.files = files
        if self.files:
            self.process_media_files()
        self.story.update(date_for=self.date_for,
                          title=self.title,
                          content=self.content,
                          user_id=self.author.id)

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

    @classmethod
    def get_by_date(cls, date_for):
        story = Story.query.filter_by(date_for=date_for).first_or_404()
        fullstory = cls(date_for=story.date_for,
                        title=story.title,
                        content=story.content,
                        story=story)
        return fullstory
