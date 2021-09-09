import logging

from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager
from os import urandom
from flask import Flask
from pymongo import MongoClient
from werkzeug.middleware.proxy_fix import ProxyFix

# Logging
logging.basicConfig(
    filename='log',
    level=logging.DEBUG,
    format='%(levelname)s %(asctime)s - %(message)s'
)
logging.getLogger().addHandler(logging.StreamHandler())  # without this errors only go to log, not stderr

# Services
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config.from_pyfile('config.py')
app.config.from_pyfile('secret.py')
app.secret_key = urandom(32)
login = LoginManager()
login.init_app(app)
oauth = OAuth(app)
oauth.register('google')
oauth.register('apple')
db = MongoClient()['db']

# Drone logic
drone = []
ports = []
errands = []

# Blueprints
from website.auth import auth
from website.pages import pages
from website.users import users
app.register_blueprint(auth)
app.register_blueprint(pages)
app.register_blueprint(users)
