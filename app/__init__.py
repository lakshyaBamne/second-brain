from datetime import datetime, timezone

from flask import Flask
from flask_login import LoginManager
from flask_wtf import CSRFProtect

from app.config import Config
from app.db import ensure_indexes, get_db
from app.models.users import get_user_by_id


def create_app(db=None, config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    app.db = db if db is not None else get_db(app.config["MONGO_URI"], app.config["MONGO_DBNAME"])
    ensure_indexes(app.db)

    CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(app.db, user_id)

    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.daily.routes import daily_bp
    from app.blueprints.dashboard.routes import dashboard_bp
    from app.blueprints.reviews.routes import reviews_bp
    from app.blueprints.settings.routes import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(daily_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(settings_bp)

    @app.context_processor
    def inject_globals():
        return {"current_year": datetime.now(timezone.utc).year}

    return app
