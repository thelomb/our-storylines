from flask_wtf import FlaskForm
from wtforms import (StringField,
                     SubmitField, TextAreaField, MultipleFileField,
                     IntegerField, SelectMultipleField, widgets,
                     RadioField, SelectField,
                     validators)
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import (DataRequired, ValidationError,
                                Length)
from application.models import User
from application import images
from wtforms.fields.html5 import DateField
from application.model_enums import TravelType, StayType


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username')


class PostForm(FlaskForm):
    # post = TextAreaField('Say something', validators=[
    #     DataRequired(), Length(min=1, max=140)])
    title = StringField('Story Title', validators=[
                        DataRequired()])
    tags = StringField('Tags')
    post = TextAreaField('Your Story', validators=[DataRequired()])
    post_images = MultipleFileField('An illustration',
                                    validators=[FileAllowed(images,
                                                            'Image Only!')])
    submit = SubmitField('Validez')

class ActivityCheckBoxes(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class ItineraryForm(FlaskForm):
    planning_description = TextAreaField('Le plan de la journée')
    # actual_description = TextAreaField("Ce que l'on a fait")
    day = DateField('Date', format='%d/%m/%Y')
    planned_start_point = StringField('Point de départ')
    planned_end_point = StringField("Point d'arrivée")
    planned_distance = IntegerField("Distance prévue")
    planned_stay = StringField("Logement")
    # actual_start_point = db.Column(db.String(132))
    # actual_end_point = db.Column(db.String(132))
    # actual_distance = db.Column(db.Integer)
    # actual_stay = db.Column(db.String(132))
    submit = SubmitField('Validez')
    activities = ActivityCheckBoxes('Les activités du jour',
                                     choices=[('plane', 'plane icon'),
                                              ('camping', 'camping icon')])


class FullStoryForm(FlaskForm):
    day = DateField('Nous sommes le: ',
                    format='%d/%m/%Y',
                    validators=[DataRequired()], id='datepick')
    title = StringField('Titre',
                        validators=[DataRequired()])
    post = TextAreaField('La journée',
                         validators=[DataRequired()])
    post_images = FileField('Les images du jour',
                            validators=[FileAllowed(images,
                                        'Image Only!')])
    start = StringField('Départ')
    end = StringField('Arrivée')
    stay = StringField('Lieu de séjour')
    odometer_read = IntegerField('Le compteur en fin de journée',
                                 [validators.optional()])
    travel_type = SelectField("Le trajet s'est effectué par:",
                             choices=TravelType.choices())
    stay_type = SelectField("Type d'hébergement:",
                             choices=StayType.choices())
    submit = SubmitField('Validez')

