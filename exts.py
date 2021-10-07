from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager
from pymongo import MongoClient
from flask_socketio import SocketIO

login = LoginManager()
oauth = OAuth()
db = MongoClient()['db']
socketio = SocketIO()
