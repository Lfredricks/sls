from flask import Blueprint

bp = Blueprint('main', __name__)

from blueprints.main import routes
