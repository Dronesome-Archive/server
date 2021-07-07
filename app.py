from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager
from os import urandom
from flask import Flask
from pymongo import MongoClient


# Services
app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config.from_pyfile('secret.py')
app.secret_key = urandom(32)
login = LoginManager()
login.init_app(app)
oauth = OAuth(app)
db = MongoClient()['app']

# Drone logic
drone = []
ports = []
missions = []

# Blueprints
from website.routes import website
app.register_blueprint(website)

