from flask import Flask
from flask_sqlalchemy import SQLAlchemy

def create_app(test_config=None):
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite"

    # Load the models
    from .models import db
    from .models.timetable import Events, Person, Fingerprints
    db.init_app(app)

    # Create the db tables
    with app.app_context():
        db.create_all()
        db.session.commit()

    # Register blueprints
    from .views.routes import api
    app.register_blueprint(api)

    return app
