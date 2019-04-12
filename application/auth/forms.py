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
