# standard library
import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler

# flask extensions
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_pagedown import PageDown
from flask_moment import Moment
from flask_googlemaps import GoogleMaps
from googlemaps import Client

# microblog
from config import Config

# instantiate extensions
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Identifiez-vous !'
login.login_message_category = 'info'
mail = Mail()
bootstrap = Bootstrap()
images = UploadSet('images', IMAGES)
pagedown = PageDown()
moment = Moment()
google_map = GoogleMaps()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    configure_uploads(app, images)
    pagedown.init_app(app)
    moment.init_app(app)
    google_map.init_app(app)

    from application.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    from application.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from application.main import bp as main_bp
    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/storylines.log',
                                           maxBytes=10240,
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s%(lineno)d]')
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Our Storylines... starting up...')

        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'],
                          app.config['MAIL_PORT']
                          ),
                fromaddr=('thelomb@' +
                          app.config['MAIL_SERVER']
                          ),
                toaddrs=app.config['ADMINS'],
                subject='Microblog Failure',
                credentials=auth,
                secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)


    return app
