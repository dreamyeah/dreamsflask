from flask import Blueprint

google = Blueprint('google', __name__)

from . import views
