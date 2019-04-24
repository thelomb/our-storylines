from flask import current_app
from application import db, login, images
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt
from markdown import markdown
import bleach
# import re
from slugify import slugify
from application.mixin import CRUDMixin
from application.model_enums import (DistanceUnit,
                                     TravelType,
                                     StayType,
                                     ImageFeature)
from sqlalchemy import Enum, func
from sqlalchemy.ext.hybrid import hybrid_property
from application.imagery import WebImage
from PIL import Image


# storyline_members = db.Table(
#     'storyline_members',
#     db.Column('member_id', db.Integer, db.ForeignKey('user.id')),
#     db.Column('storyline_id', db.Integer, db.ForeignKey('storyline.id')),
# )

class StorylineMembership(db.Model):
    storyline_id = db.Column(db.Integer,
                             db.ForeignKey('storyline.id'),
                             primary_key=True)
    member_id = db.Column(db.Integer,
                          db.ForeignKey('user.id'),
                          primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_contributor = db.Column(db.Boolean, default=False)
    is_visitor = db.Column(db.Boolean, default=False)
    member = db.relationship('User', back_populates='storylines')
    storyline = db.relationship('Storyline', back_populates='members')


story_tags = db.Table(
    'story_tags',
    db.Column('story_id', db.Integer, db.ForeignKey('story.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)


class Storyline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True, nullable=False)
    description = db.Column(db.String(140))
    stories = db.relationship('Story', backref='storyline', lazy='dynamic')
    members = db.relationship(
        'StorylineMembership',
        back_populates="storyline",
        lazy='dynamic')
    slug = db.Column(db.String(32), index=True, nullable=False)
    start_date = db.Column(db.Date, index=True, unique=True)
    end_date = db.Column(db.Date, index=True, unique=True)

    def add_member(self,
                   user,
                   is_admin=False,
                   is_contributor=False,
                   is_visitor=True):
        if user.id:
            if self.is_member(user):
                return
        user_role = StorylineMembership(member=user,
                                        is_admin=is_admin,
                                        is_contributor=is_contributor,
                                        is_visitor=is_visitor)
        self.members.append(user_role)

    def remove_member(self, user):
        if self.is_member(user):
            self.members.remove(user)
            if user.current_line_id == self.id:
                user.current_line_id = None

    def is_member(self, user):
        return self.members.filter(StorylineMembership.member == user and
                                   StorylineMembership.storyline == self
                                   ).count() > 0

    def is_contributor(self, user):
        return self.members.filter(StorylineMembership.member == user and
                                   StorylineMembership.storyline == self and
                                   StorylineMembership.is_contributor
                                   ).count() > 0

    def is_admin(self, user):
        return self.members.filter(StorylineMembership.member == user and
                                   StorylineMembership.storyline == self and
                                   StorylineMembership.is_admin
                                   ).count() > 0

    @staticmethod
    def on_changed_name(target, value, oldvalue, initiator):
        target.slug = slugify(value)

    def pictures(self):
        media = []
        for story in self.stories.order_by(Story.date_for.asc()):
            for medium in story.media:
                if medium.feature == ImageFeature.FEATURED:
                    media.append(medium)
        return media

    def nb_stories_in_trip(self):
        return self.stories.filter(Story.date_for >= self.start_date,
                                   Story.date_for <= self.end_date).count()

    @staticmethod
    def last_entry():
        return db.session.query(func.max(Story.date_for)).first()[0]




db.event.listen(Storyline.name, 'set', Storyline.on_changed_name)


class User(UserMixin, CRUDMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    # stories = db.relationship('Story', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    current_line_id = db.Column(db.Integer, db.ForeignKey('storyline.id'))
    storylines = db.relationship('StorylineMembership',
                                 back_populates='member',
                                 lazy='dynamic')
    picture_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    picture = db.relationship('Media',
                              uselist=False,
                              backref='user',
                              cascade="all, delete-orphan",
                              single_parent=True)

    def __repr__(self):
        return '<The user is {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        # digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        digest = md5('toto'.encode('utf-8')).hexdigest()
        return ('http://www.gravatar.com/avatar/{}?d=identicon&s={}'.
                format(digest, size))

    def current_storyline(self):
        return Storyline.query.filter_by(id=self.current_line_id).first()

    def roles_in_storyline(self, storyline=None):
        """
        Return the user's roles for in a specific Storyline defined in
        StorylineMembership. If no storyline is given, the current user
        storyline is used

        Keyword argument:
        storyline -- a storyline (default None for current storyline)
        """
        if storyline is None:
            storyline_id = self.current_line_id
        else:
            storyline_id = storyline.id

        return StorylineMembership.query.filter_by(
            storyline_id=storyline_id,
            member_id=self.id).first()

    def get_reset_password_token(self, expires_in=172800):
        token = jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode(
            'utf-8')
        return token

    @staticmethod
    def verify_reset_password_token(token):
        id = jwt.decode(token, current_app.config['SECRET_KEY'],
                        alorithms=['HS256'])['reset_password']
        return User.query.get(id)

    def update(self,
               username,
               about_me,
               file):
        self.username = username
        self.about_me = about_me
        if len(file) == 1:
            image_info = file[0]
            if self.picture:
                if self.picture.request_file_name == image_info.filename:
                        return
            filename = images.save(image_info)
            path = images.path(filename)
            url = images.url(filename)
            url = url.replace('http://', 'https://')
            web_image = WebImage(Image.open(path))
            web_image.fix_orientation()
            web_image.save(path)
            thumbnail = web_image.square_thumbnail()
            thumb_name = '128x128_' + filename
            thumb_url = url.replace(filename, thumb_name)
            thumb_path = path.replace(filename, thumb_name)
            thumbnail.save(thumb_path)

            image = Media(name=thumb_name,
                          filename=thumb_name,
                          url=thumb_url,
                          type='Image',
                          request_file_name=image_info.filename,
                          location=None,
                          exif_width=web_image.exif_width,
                          exif_height=web_image.exif_height)
            web_image.close()
            self.picture = image


class Story(db.Model, CRUDMixin):
    id = db.Column(db.Integer, primary_key=True)
    date_for = db.Column(db.Date, index=True, unique=True)
    title = db.Column(db.String(140), index=True)
    content = db.Column(db.Text)
    html_content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
                           foreign_keys=[user_id],
                           single_parent=True)
    storyline_id = db.Column(db.Integer, db.ForeignKey('storyline.id'))
    tags = db.relationship(
        'Tag',
        secondary=story_tags,
        back_populates="stories",
        lazy='dynamic')
    media = db.relationship('Media',
                            backref='story',
                            lazy='dynamic',
                            cascade="all, delete-orphan")
    stay_id = db.Column(db.Integer, db.ForeignKey('geo_point.id'))
    stay = db.relationship('GeoPoint',
                           uselist=False,
                           backref='story',
                           cascade="all, delete-orphan",
                           single_parent=True)
    stay_type = db.Column(Enum(StayType), default='HOTEL')
    stay_description = db.Column(db.Text)
    itinerary = db.relationship('Itinerary',
                                uselist=False,
                                backref='story',
                                cascade="all, delete-orphan")
    comments = db.relationship('Comment',
                               backref='story',
                               lazy='dynamic',
                               cascade="all, delete-orphan")
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    friend = db.relationship('User',
                             foreign_keys=[friend_id],
                             single_parent=True)

    def __repr__(self):
        return '<Story id: {}, title {}>'.format(self.id, self.title)

    @staticmethod
    def on_changed_content(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p', 'img']
        bleach.sanitizer.ALLOWED_ATTRIBUTES['img'] = ['alt', 'src', 'class']
        target.html_content = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def in_trip_story(self):
        return self.date_for >= self.storyline.start_date

    def excerpt(self):
        return self.content[:100]


db.event.listen(Story.content, 'set', Story.on_changed_content)


class Media(db.Model, CRUDMixin):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(32), index=True)
    name = db.Column(db.String(140))
    filename = db.Column(db.String(140))
    url = db.Column(db.String(1400))
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'))
    related_story = db.relationship('Story')
    location_id = db.Column(db.Integer, db.ForeignKey('geo_point.id'))
    location = db.relationship('GeoPoint',
                               uselist=False,
                               backref='media',
                               cascade="all, delete-orphan",
                               single_parent=True)
    request_file_name = db.Column(db.String(256))
    exif_width = db.Column(db.Integer)
    exif_height = db.Column(db.Integer)
    comment = db.Column(db.String(1000))
    feature = db.Column(Enum(ImageFeature), default='NONE')
    resized_url = db.Column(db.String(1400))

    def __init__(self,
                 name,
                 filename,
                 url,
                 type,
                 request_file_name,
                 location,
                 resized_url=None,
                 exif_width=1,
                 exif_height=1):
        self.name = name
        self.filename = filename
        self.url = url
        self.resized_url = resized_url
        self.type = type
        self.request_file_name = request_file_name
        self.location = location
        self.exif_width = exif_width
        self.exif_height = exif_height

    @hybrid_property
    def image_ratio(self):
        return self.exif_width / self.exif_height


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True, nullable=False)
    slug = db.Column(db.String(32), index=True, nullable=False)
    stories = db.relationship(
        'Story',
        secondary=story_tags,
        back_populates='tags',
        lazy='dynamic')

    @staticmethod
    def on_changed_name(target, value, oldvalue, initiator):
        target.slug = slugify(value)


db.event.listen(Tag.name, 'set', Tag.on_changed_name)


class Itinerary(db.Model, CRUDMixin):
    id = db.Column(db.Integer, primary_key=True)
    travel_type = db.Column(Enum(TravelType), default='CAR')
    odometer_at = db.Column(db.Integer, default=0)
    odometer_scale = db.Column(Enum(DistanceUnit), default='MILE')
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'))
    start_point_id = db.Column(db.Integer, db.ForeignKey("geo_point.id"))
    end_point_id = db.Column(db.Integer, db.ForeignKey("geo_point.id"))
    start = db.relationship('GeoPoint',
                            foreign_keys=[start_point_id],
                            cascade="all, delete-orphan",
                            single_parent=True)
    end = db.relationship('GeoPoint',
                          foreign_keys=[end_point_id],
                          cascade="all, delete-orphan",
                          single_parent=True)
    # intermediary_points = db.relationship('GeoPoint',
    #                                       backref='itinerary',
    #                                       lazy='dynamic')


class GeoPoint(db.Model, CRUDMixin):
    id = db.Column(db.Integer, primary_key=True)
    place = db.Column(db.String(140))
    latitude = db.Column(db.Float())
    longitude = db.Column(db.Float())
    formatted_address = db.Column(db.String(140))
    # story_id = db.Column(db.Integer, db.ForeignKey('story.id'))
    # intermediary_point = db.relationship('Itinerary')


class Comment(db.Model, CRUDMixin):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    html_content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User',
                             foreign_keys=[author_id],
                             single_parent=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'))

    @staticmethod
    def on_changed_content(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p', 'img']
        bleach.sanitizer.ALLOWED_ATTRIBUTES['img'] = ['alt', 'src', 'class']
        target.html_content = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))


db.event.listen(Comment.content, 'set', Comment.on_changed_content)


# Mixin flask login
@login.user_loader
def load_user(id):
    return User.query.get(int(id))
