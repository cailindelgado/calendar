from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy

def create_app(test_config=None):
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite"

    if test_config is not None:
        app.config.update(test_config)

    # Load the models
    from .models import db
    from .models.timetable import Events, Person, Fingerprints
    db.init_app(app)

    # Create the db tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    from .views.routes import api
    app.register_blueprint(api)

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    return app
