from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager
from os import urandom
from flask import Flask
from pymongo import MongoClient

from user import User
from website.routes import website


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
app.register_blueprint(website)


# Create user object from db for flask_login
@login.user_loader
def load_user(login_id):
    user = db.users.find_one({'login_id': login_id})
    if not user:
        return None
    else:
        return User(user)
