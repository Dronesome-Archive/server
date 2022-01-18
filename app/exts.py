from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager
from pymongo import MongoClient
from flask_socketio import SocketIO

login = LoginManager()
oauth = OAuth()
db = MongoClient()['db']
socketio = SocketIO(logger=True, engineio_logger=True, ping_interval=10, ping_timeout=10)
