from application import db, create_app
from application.models import (User,
                                Story,
                                Storyline,
                                Media,
                                Itinerary,
                                GeoPoint,
                                StorylineMembership)
from application.email import send_password_reset_email, send_email

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db,
            'User': User,
            'Story': Story,
            'Storyline': Storyline,
            'Media': Media,
            'Itinerary': Itinerary,
            'GeoPoint': GeoPoint,
            'StorylineMembership': StorylineMembership,
            'send_password_reset_email': send_password_reset_email,
            'send_email': send_email}
