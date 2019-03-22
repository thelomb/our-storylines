from application import images
from application.models import Story, Media


class Fullstory():

    def __init__(self, date_for, title, post, start, end, stay,
                 odometer_at, travel_type, author, files):
        self.date_for = date_for
        self.title = title
        self.content = post
        self.start = start
        self.end = end
        self.stay = stay
        self.odometer_at = odometer_at
        self.travel_type = travel_type
        self.author = author
        self.files = files
        self.media_request()

    def store(self):
        Story.create(date_for=self.date_for,
                     title=self.title,
                     content=self.content,
                     user_id=self.author.id,
                     media=self.media['photo'])
        print('story created!')

    def media_request(self):
            photos = []
            # audios = []
            # videos = []
            media = {
                'photo': [],
                # 'video': [],
                # 'audio': []
            }
            if self.files:
                for image_info in self.files:
                    filename = images.save(image_info)
                    url = images.url(filename)
                    image = Media(name=filename,
                                  filename=filename,
                                  url=url,
                                  type='Image')
                    photos.append(image)
                    media['photo'] = photos
            self.media = media
