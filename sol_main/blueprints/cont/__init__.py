from flask import Blueprint

bp = Blueprint('cont', __name__)

from blueprints.cont import routes
