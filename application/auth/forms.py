from flask_wtf import FlaskForm
from wtforms import (StringField,
                     PasswordField,
                     BooleanField,
                     SubmitField)
from wtforms.validators import (DataRequired,
                                EqualTo)


class LoginForm(FlaskForm):
    username = StringField('Utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Choisissez votre mot de passe',
                             validators=[DataRequired()])
    password_repeat = PasswordField('Répétez le mot de passe',
                                    validators=[DataRequired(),
                                                EqualTo('password')])
    submit = SubmitField('Sauvez le mot de passe')

# class RegistrationForm(FlaskForm):
#     username = StringField('Username', validators=[DataRequired()])
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     password = PasswordField('Password', validators=[DataRequired()])
#     password_repeat = PasswordField(
#         'Repeat Password', validators=[DataRequired(), EqualTo('password')])
#     submit = SubmitField('Register')

#     def validate_username(self, username):
#         user = User.query.filter_by(username=username.data).first()
#         if user is not None:
#             raise ValidationError('Please use a different username')

#     def validate_email(self, email):
#         user = User.query.filter_by(email=email.data).first()
#         if user is not None:
#             raise ValidationError('Please use a different email address')


# class ResetPasswordRequestForm(FlaskForm):
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     submit = SubmitField('Request Password Reset')


