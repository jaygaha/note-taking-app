# the create_app() factory function

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from app.utils import md_to_html, human_readable_date

# Init extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_class=Config):
    # Create the app instance
    app = Flask(__name__)
    # Load configuration from the config class
    app.config.from_object(config_class)

    # Bind extensions to app instance
    db.init_app(app)
    migrate.init_app(app, db)


    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # the view function that handles login
    
    # Register blueprints
    from app.main.routes import main_bp
    app.register_blueprint(main_bp)

    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.notes import notes_bp
    app.register_blueprint(notes_bp, url_prefix='/notes')
    
    # Register the custom filter
    app.jinja_env.filters['markdown'] = md_to_html
    app.jinja_env.filters['human_readable_date'] = human_readable_date

    return app