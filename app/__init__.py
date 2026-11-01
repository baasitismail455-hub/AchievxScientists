import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

load_dotenv()
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    upload_dir = Path(app.instance_path) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-this-secret-before-deployment"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL") or
            f"sqlite:///{Path(app.instance_path) / 'achievx_scientist.db'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        UPLOAD_FOLDER=str(upload_dir),
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_CONTENT_LENGTH_MB", "100")) * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_HTTPONLY=True,
    )
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth_login"
    login_manager.login_message = "Please sign in to continue."
    login_manager.login_message_category = "info"

    from app import routes
    routes.register_routes(app)

    with app.app_context():
        db.create_all()

    return app
