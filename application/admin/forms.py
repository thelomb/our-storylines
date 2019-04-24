from flask_wtf import FlaskForm
from wtforms import (TextAreaField,
                     SubmitField)
from wtforms.validators import (DataRequired)


class GeneralEmailAll(FlaskForm):
    email = TextAreaField('Email', validators=[DataRequired()])
    submit = SubmitField('Envoyez')
