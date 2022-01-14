from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app import log
import app.drones
from app.exts import oauth, login, socketio
from app.blueprints import blueprints

# GENERAL GUIDELINES:
# 1. Design the frontend so that an unsuspecting user can't generate faulty input.
# 2. Only catch errors generated by faulty user input and return a generic error message.
# 3. Don't catch potential errors from our own API or database.
# 4. For naming, only use 'state', never 'status'
# 5. For UI text use double quotes, for internal strings use single quotes


def init_exts(flaskApp):
    flaskApp.wsgi_app = ProxyFix(flaskApp.wsgi_app)
    oauth.init_app(flaskApp)
    for server in flaskApp.config['OAUTH_SERVERS']:
        oauth.register(server)
    login.init_app(flaskApp)
    socketio.init_app(flaskApp)


def register_blueprints(flaskApp):
    for blueprint in blueprints:
        flaskApp.register_blueprint(blueprint)


def create_app(config_objects):
    flaskApp = Flask(__name__)
    for obj in config_objects:
        flaskApp.config.from_object(obj)
    init_exts(flaskApp)
    app.drones.init()
    register_blueprints(flaskApp)
    return flaskApp
