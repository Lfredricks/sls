from flask import Blueprint

bp = Blueprint('vend', __name__)

from blueprints.vend import routes
