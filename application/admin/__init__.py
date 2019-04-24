from flask import Blueprint

bp = Blueprint('admin', __name__)

from application.admin import routes
