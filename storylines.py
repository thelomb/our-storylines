from application import db, create_app
from application.models import User, Story, Storyline, Media, Tag

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Story': Story, 'Storyline': Storyline, 'Media': Media, 'Tag': Tag}
