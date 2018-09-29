from flask_wtf import FlaskForm
from wtforms import (StringField,
                     SubmitField, TextAreaField, MultipleFileField)
from wtforms.validators import (DataRequired, ValidationError,
                                Length)
from application.models import User
from flask_wtf.file import FileField, FileAllowed, FileRequired
from application import images
from flask_pagedown.fields import PageDownField


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
    post = TextAreaField('Your Story', validators=[
                       DataRequired()])
    post_images = MultipleFileField('An illustration',
                                    validators=[FileAllowed(images,
                                                            'Image Only!')])
    submit = SubmitField('Validez')
