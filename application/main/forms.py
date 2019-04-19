from flask_wtf import FlaskForm
from wtforms import (StringField,
                     SubmitField,
                     TextAreaField,
                     IntegerField,
                     SelectField,
                     validators)
from wtforms.widgets import HiddenInput
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import (DataRequired,
                                ValidationError,
                                Length,
                                Optional)
from application.models import User, Story
from application import images
from wtforms.fields.html5 import DateField
from application.model_enums import TravelType, StayType


class Unique(object):
    """ validator that checks field uniqueness"""

    def __init__(self, model, field, message=None):
        self.model = model
        self.field = field
        if not message:
            message = 'this element already exists'
        self.message = message

    def __call__(self, form, field):
        check = self.model.query.filter(self.field == field.data).first()
        if check:
            if check.id != form.id.data:
                raise ValidationError(self.message)


class EditProfileForm(FlaskForm):
    message = "Je sais que vous aimez beaucoup parler de vous - Guerre et Paix attendra 🤓. Pas plus long qu'un tweet!"
    username = StringField("Nom d'Utilisateur", validators=[DataRequired()])
    about_me = TextAreaField('Décrivez-vous en 140 charactères',
                             validators=[Length(min=0,
                                                max=130,
                                                message=message)])
    picture = FileField('Une image de vous',
                        validators=[FileAllowed(images,
                                    'Image Only!')],
                        render_kw={'multiple': False})
    submit = SubmitField('Sauvez')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError("Ce nom d'utilisateur est déjà pris 😕 Choisissez en un autre!")


class FullStoryForm(FlaskForm):
    id = IntegerField(widget=HiddenInput(),
                      validators=[Optional()])
    day = DateField('Nous sommes le: ',
                    format='%d/%m/%Y',
                    validators=[DataRequired(),
                                Unique(Story,
                                       Story.date_for,
                                       'Une seule entrée par jour!')],
                    id='datepick')
    title = StringField('Titre',
                        validators=[DataRequired()])
    post = TextAreaField('La journée',
                         validators=[DataRequired()], render_kw={'rows': '19'})
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
    stay_description = TextAreaField('Description du lieu de séjour',
                                     render_kw={'placeholder':
                                        'Comment était le séjour, chez qui?'})
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


class CommentForm(FlaskForm):
    message = 'Votre commentaire est trop long - Guerre et Paix attendra 🤓'
    comment = TextAreaField('Votre commentaire',
                            validators=[Length(min=0,
                                               max=900,
                                               message=message)],
                            render_kw={'placeholder':
                                       'Ajouter votre commentaire...',
                                       'class': 'btn-primary'})
    submit = SubmitField('Sauvez')
