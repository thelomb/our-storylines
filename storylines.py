from application import db, create_app, moment
from application.models import User, Story, Storyline, Media, Tag, Itinerary

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Story': Story, 'Storyline': Storyline, 'Media': Media, 'Tag': Tag, 'Itinerary':Itinerary, 'moment': moment}
