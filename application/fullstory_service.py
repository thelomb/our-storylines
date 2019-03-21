from application import images
from application.models import Story, Media


def media_request(media_request):
        photos = []
        # audios = []
        # videos = []
        media = {
            'photo': [],
            # 'video': [],
            # 'audio': []
        }
        if media_request:
            for image_info in media_request.getlist('post_images'):
                filename = images.save(image_info)
                url = images.url(filename)
                image = Media(name=filename,
                              filename=filename,
                              url=url,
                              type='Image')
                photos.append(image)
                media['photo'] = photos
        return media


class Fullstory():
    @classmethod
    def create(cls, fullstory, author, files):
        Story.create(date_for=fullstory['date_for'],
                     title=fullstory['title'],
                     content=fullstory['post'],
                     user_id=author.id,
                     media=media_request(files)['photo']
                     )
        print('story created!')
