from flask import current_app
from application import db, login
from datetime import datetime
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
from application.model_enums import DistanceUnit, TravelType
from sqlalchemy import Enum


storyline_members = db.Table(
    'storyline_members',
    db.Column('member_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('storyline_id', db.Integer, db.ForeignKey('storyline.id'))
)


story_tags = db.Table(
    'story_tags',
    db.Column('story_id', db.Integer, db.ForeignKey('story.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)


class Storyline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True, nullable=False)
    description = db.Column(db.String(140))
    administrator_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                                 nullable=True)
    stories = db.relationship('Story', backref='storyline', lazy='dynamic')
    members = db.relationship(
        'User',
        secondary=storyline_members,
        back_populates="memberships",
        lazy='dynamic')

    def add_member(self, user):
        print('add member')
        if not self.is_member(user):
            self.members.append(user)
            if not user.current_line_id:
                user.current_line_id = self.id

    def remove_member(self, user):
        if self.is_member(user):
            self.members.remove(user)
            if user.current_line_id == self.id:
                user.current_line_id = None
            # TO DO deal with user stories

    def set_administrator(self, user):
        print('set admin')
        if not self.administrator_id:
            self.administrator_id = user.id

            # admin becomes member automatically
            self.add_member(user)

    def is_member(self, user):
        return self.members.filter(
            storyline_members.c.member_id == user.id).count() > 0

    def linked_stories(self):
        return (Story.query.filter_by(storyline_id=self.id)
                .order_by(Story.timestamp.desc()))

    def daily_stories(self, day):
        return (Story.query.filter(storyline_id=self.id)
                .order_by(Story.timestamp.desc()))


class User(UserMixin, CRUDMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    stories = db.relationship('Story', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    current_line_id = db.Column(db.Integer, db.ForeignKey('storyline.id'))
    memberships = db.relationship(
        'Storyline',
        secondary=storyline_members,
        back_populates='members',
        lazy='dynamic')

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

    # def follow(self, user):
    #     if not self.is_following(user):
    #         self.followed.append(user)

    # def unfollow(self, user):
    #     if self.is_following(user):
    #         self.followed.remove(user)

    # def is_following(self, user):
    #     return self.followed.filter(
    #         followers.c.followed_id == user.id).count() > 0

    #
    #SQL equivalent:
    #SELECT
    #    p.*
    #FROM
    #   post p
    #JOIN
    #   followers f
    #ON
    #   f.followed_id=p.user_id
    #WHERE
    #   f.follower_id=(select id from User where id=me)
    #ORDER BY
    #   p.timestamp DESC
    # def followed_posts(self):
    #     followed = Post.query.join(
    #         followers, (followers.c.followed_id == Post.user_id)).filter(
    #             followers.c.follower_id == self.id)
    #     own = Post.query.filter_by(user_id=self.id)
    #     return followed.union(own).order_by(Post.timestamp.desc())

    # def followed_posts_sql(self):
    #     statement = """
    #         SELECT p.* FROM post p JOIN
    #         followers f ON f.followed_id=p.user_id
    #         WHERE f.follower_id=:id
    #         UNION
    #         select p.* from post p where p.user_id=:id
    #         ORDER BY p.timestamp DESC
    #         """
    #     sql = text(statement)
    #     out = db.engine.execute(sql, id=self.id)
    #     return out

    def get_reset_password_token(self, expires_in=600):
        token = jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode(
            'utf-8')
        print(token)
        return token

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            alorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class Story(db.Model, CRUDMixin):
    id = db.Column(db.Integer, primary_key=True)
    date_for = db.Column(db.Date, index=True)
    title = db.Column(db.String(140), index=True)
    content = db.Column(db.Text)
    html_content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    storyline_id = db.Column(db.Integer, db.ForeignKey('storyline.id'))
    stay_id = db.Column(db.Integer, db.ForeignKey('geo_point.id'))
    # image_filename = db.Column(db.String)
    # image_url = db.Column(db.String)
    tags = db.relationship(
        'Tag',
        secondary=story_tags,
        back_populates="stories",
        lazy='dynamic')
    media = db.relationship('Media', backref='story', lazy='dynamic')
    # itinerary = db.relationship('Itinerary', backref='story', lazy='dynamic')

    def __repr__(self):
        return '<Story id: {}, title {}>'.format(self.id, self.title)

    # def __init__(self, **kwargs):

    #     print('init story speaking')
    #     self.date_for = kwargs['form'].day.data
    #     self.title = kwargs['form'].title.data
    #     self.content = kwargs['form'].post.data
    #     self.user_id = kwargs['user'].id

    #     # create file reference
    #     for medium in kwargs['media']['photo']:
    #         Media.create(type='Image', name=medium['filename'],
    #                      filename=medium['filename'], url=medium['url'],
    #                      related_story=self)

    #     # itinerary
    #     print('User is: ', kwargs['user'])
    #     if kwargs['form'].travel_type.data == TravelType.NONE.name:
    #         stay = GeoPoint.create(place=kwargs['form'].start.data)
    #         self.stay_id = stay.id
    #     elif (kwargs['form'].travel_type.data != TravelType.NONE.name and
    #           kwargs['form'].start.data is not None and
    #           kwargs['form'].end.data is not None):
    #         Itinerary.create(start=kwargs['form'].start.data,
    #                          end=kwargs['form'].end.data,
    #                          odometer_at=kwargs['form'].odometer_read.data,
    #                          travel_type=kwargs['form'].travel_type.data)

    @staticmethod
    def on_changed_content(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p', 'img']
        bleach.sanitizer.ALLOWED_ATTRIBUTES['img'] = ['alt', 'src', 'class']
        target.html_content = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    # def update(self, **kwargs):
    #     print(kwargs)
    #     for attr, value in kwargs.items():
    #         setattr(self, attr, value)

    #     return self.save()


db.event.listen(Story.content, 'set', Story.on_changed_content)


class Media(db.Model, CRUDMixin):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(32), index=True)
    name = db.Column(db.String(140))
    filename = db.Column(db.String(140))
    url = db.Column(db.String(1400))
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'))
    related_story = db.relationship('Story')


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
    odometer_at = db.Column(db.Integer)
    odometer_scale = db.Column(Enum(DistanceUnit), default='MILE')
    start_point_id = db.Column(db.Integer, db.ForeignKey('geo_point.id'))
    end_point_id = db.Column(db.Integer, db.ForeignKey('geo_point.id'))
    start = db.relationship('GeoPoint', foreign_keys=[start_point_id])
    end = db.relationship('GeoPoint', foreign_keys=[end_point_id])
    # intermediary_points = db.relationship('GeoPoint',
    #                                       backref='itinerary',
    #                                       lazy='dynamic')
    # story_id = db.Column(db.Integer, db.ForeignKey('story.id'))
    # related_story = db.relationship('Story')

    def __init__(self, start, end, odometer_at, travel_type, **kwargs):
        startPoint = GeoPoint.create(place=start)
        endPoint = GeoPoint.create(place=end)
        self.start_point_id = startPoint.id
        self.end_point_id = endPoint.id
        self.odometer_at = odometer_at
        self.travel_type = TravelType[travel_type]


class GeoPoint(db.Model, CRUDMixin):
    id = db.Column(db.Integer, primary_key=True)
    place = db.Column(db.String(32))
    latitude = db.Column(db.Float())
    longitude = db.Column(db.Float())
    formatted_address = db.Column(db.String(140))
    # intermediary_point = db.relationship('Itinerary')


# Mixin flask login
@login.user_loader
def load_user(id):
    return User.query.get(int(id))
