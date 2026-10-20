from blueprints.main import bp
from flask import render_template

@bp.route('/')
@bp.route('/home')
def home():
    return render_template('main/home.html')


@bp.route('/about')
def about():
    return render_template('main/about.html', title='About')
