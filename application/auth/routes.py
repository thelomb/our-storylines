from flask import (render_template,
                   flash,
                   redirect,
                   url_for,
                   request,
                   current_app)
from application import db
from application.auth import bp
from application.auth.forms import (LoginForm,
                                    ResetPasswordForm)
from flask_login import current_user, login_user, logout_user, login_required
from application.models import User
from werkzeug.urls import url_parse
from application.email import send_password_reset_email
from application.helpers import admin_only
import jwt


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        # flash('Vous êtes maintenant connecté et pouvez suivre les Boulombs',
        #      'info')
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Mot de passe invalide')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        print('next page:', next_page)
        return redirect(next_page)
    return render_template('auth/login.html',
                           title='Sign In',
                           form=form,
                           website='Our Storylines')


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@bp.route('/reset_password_request/<username>', methods=['GET'])
@login_required
@admin_only
def reset_password_request(username):
    user = User.query.filter_by(username=username).first()
    if user:
        send_password_reset_email(user)
        flash('Email sent to ' + username + ' at ' + user.email, 'info')
    return redirect(url_for('main.storyline_community',
                            storyline=user.current_storyline().slug))


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    try:
        user = User.verify_reset_password_token(token)
    except jwt.exceptions.ExpiredSignatureError:
        return render_template('expired_token.html', title='Invalidation\
                               de votre adresse email')
    if not user:
        current_app.logger.warning('user tried to set new\
                                   password with invalid or expired token')
        return redirect(url_for('auth.login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        # flash('Vous voilà à nouveau connecté!')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
