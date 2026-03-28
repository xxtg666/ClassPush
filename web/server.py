import logging
from flask import Flask

logger = logging.getLogger("classpush.web")


def create_app(message_manager, config):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = "classpush-secret-key"
    app.config["MM"] = message_manager
    app.config["CONFIG"] = config

    from web.routes import api_bp

    app.register_blueprint(api_bp)

    from web.routes import web_bp

    app.register_blueprint(web_bp)

    return app
