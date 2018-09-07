from flask import current_app
from application import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from sqlalchemy import text
from time import time
import jwt
from markdown import markdown
import bleach


storyline_members = db.Table(
    'storyline_members',
    db.Column('member_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('storyline_id', db.Integer, db.ForeignKey('storyline.id'))
)


class Storyline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True)
    description = db.Column(db.String(1000))
    administrator_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                                 nullable=True)
    stories = db.relationship('Story', backref='storyline', lazy='dynamic')
    members = db.relationship(
        'User',
        secondary=storyline_members,
        back_populates="memberships",
        lazy='dynamic')

    def add_member(self, user):
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


class User(UserMixin, db.Model):
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
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
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
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')
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


class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), index=True)
    content = db.Column(db.String(140))
    html_content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # date_for = db.Column(db.Date, index=True, default=timestamp)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    storyline_id = db.Column(db.Integer, db.ForeignKey('storyline.id'))
    image_filename = db.Column(db.String)
    image_url = db.Column(db.String)

    def __repr__(self):
        return '<Story {}>'.format(self.body)

    @staticmethod
    def on_changed_content(target, value, oldvalue, initiator):
        print("on changed content")
        print(markdown(value, output_format='html'))
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p', 'img']
        bleach.sanitizer.ALLOWED_ATTRIBUTES['img'] = ['alt', 'src', 'class']
        target.html_content = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))


db.event.listen(Story.content, 'set', Story.on_changed_content)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
