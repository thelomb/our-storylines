from flask_wtf import FlaskForm
from wtforms import (StringField,
                     SubmitField,
                     TextAreaField,
                     IntegerField,
                     SelectField,
                     validators)
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import (DataRequired,
                                ValidationError,
                                Length,
                                Optional,
                                Required)
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
    stay = StringField('Lieu de séjour',
                       validators=[DataRequired()])
    stay_type = SelectField("Type d'hébergement:",
                            choices=StayType.choices())
    start = StringField('Départ')
    end = StringField('Arrivée')
    odometer_read = StringField('Le compteur en fin de journée')
    travel_type = SelectField("Le trajet s'est effectué par:",
                              choices=TravelType.choices())
    submit = SubmitField('Validez')

    def validate_end(self, field):
        message = 'Si vous commencez ou finissez quelque part, \
                   il faut que vous finissiez ou commenciez votre itinéraire 😜'
        if ((self.start.data == '' and self.end.data != '') or
                (self.start.data != '' and self.end.data == '')):
            raise ValidationError(message)

    def validate_odometer_read(self, field):
        message_missing_data = 'Si vous faîtes le trajet en voiture, ce serait bien \
                  de noter les kilomètres (ok, les miles 🤓)'
        message_value_error = 'Entrée invalide... 🧐'
        if field.data and self.travel_type.data == TravelType.CAR.name:
            try:
                int(field.data)
            except ValueError:
                raise ValidationError(message_value_error)
        elif field.data == '' and self.travel_type.data == TravelType.CAR.name:
            raise ValidationError(message_missing_data)
