from functools import wraps
from flask import request, redirect, url_for
from flask_login import current_user


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
