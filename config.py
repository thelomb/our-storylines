import os
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOADED_IMAGES_DEST = os.path.join(basedir, 'static', 'images')
    STORIES_PER_PAGE = 3
    ITINERARIES_PER_PAGE = 25
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT') or 25
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    ADMINS = 'pascal.lombardet@gmail.com'
    MAIL_USE_TLS = True
    GOOGLEMAPS_KEY = os.environ.get('GOOGLEMAPS_KEY')
