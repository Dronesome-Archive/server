import random
import string
import datetime

from werkzeug.utils import redirect
from authlib.integrations.flask_client import OAuth
from flask_login import current_user, LoginManager, login_required
from os import urandom
import flask_login
import markupsafe
import flask
import pymongo
import bson

import mission
import drone 

# App setup
app = flask.Flask(__name__)
app.config.from_pyfile('config.py')
app.config.from_pyfile('secret.py')
app.secret_key = urandom(32)
login = LoginManager()
login.init_app(app)
oauth = OAuth(app)
db = pymongo.MongoClient()['app']

# Drone logic setup
drone = []
ports = []
missions = []


################################################################################
# WEB APP API
################################################################################




################################################################################
# WEB APP PAGES
################################################################################


# Drone management page
@app.route('/courier')
def courier():
	pass


# Login page
@app.route('/login')
def login():
	pass


# Register new user
@app.route('/register')
def register_user():
	pass