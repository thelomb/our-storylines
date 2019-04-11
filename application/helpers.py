from functools import wraps
from flask import request, redirect, url_for, abort
from flask_login import current_user
from application.models import Storyline


def admin_only(f):
    """
    Decorator function for functions only callable by admin user
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.roles_in_storyline().is_admin:
            return redirect(url_for(request.url))
        return f(*args, **kwargs)

    return decorated_function


def authorized_storyline(f):
    """
    Decorator function to prevent user not members of the
    storyline to connect to a storyline
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        storyline_slug = kwargs.get('storyline', None)
        if storyline_slug is None:
            return redirect(url_for('main.index',
                                    storyline=current_user.
                                    current_storyline().slug))
        else:
            storyline = Storyline.query.filter_by(slug=storyline_slug).first()
            if storyline is None:
                return abort(404)
        if not current_user.current_line_id == storyline.id:
            return abort(404)  # TODO redirect to user page
        return f(*args, **kwargs)

    return decorated_function
