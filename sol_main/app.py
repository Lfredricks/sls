from flask import Flask
from config import Config
from extensions import db, migrate, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    import models  # noqa: F401 — ensures models are registered with SQLAlchemy metadata

    from blueprints.main import bp as main_bp
    from blueprints.cont import bp as cont_bp
    from blueprints.vend import bp as vend_bp
    from blueprints.admin import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(cont_bp)
    app.register_blueprint(vend_bp)
    app.register_blueprint(admin_bp)

    return app


@login_manager.user_loader
def load_user(user_id):
    from models import AdminUser
    return AdminUser.query.get(int(user_id))


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
