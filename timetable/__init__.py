from flask import Flask

def create_app(test_config=None, config_overrides=None):
    app = Flask(__name__)

    from .views.routes import api
    app.register_blueprint(api)

    return app
