from flask import (render_template,
                   flash,
                   redirect,
                   url_for,
                   request,
                   current_app)
from application import db
from application.admin import bp
from flask_login import login_required
from application.helpers import admin_only, authorized_storyline
from application.models import (User,
                                Story,
                                Media,
                                Storyline,
                                StorylineMembership)
from application.admin.forms import (GeneralEmailAll)
from application.email import send_general_email


@bp.route('/<storyline>/admin/email', methods=['GET', 'POST'])
@login_required
@authorized_storyline
@admin_only
def send_email(storyline):
    form = GeneralEmailAll()
    sl = Storyline.query.filter_by(slug=storyline).first()
    if form.validate_on_submit():
        users = ['pascal.lombardet@gmail.com']
        send_general_email(subject=sl.name,
                           recipients_email=users,
                           text_body='',
                           html_body=form.email)
        form.email.data=None
    return render_template('admin/send_email.html',
                           title='Admin - Email',
                           storyline=sl,
                           form=form)
