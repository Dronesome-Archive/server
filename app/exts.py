from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager
from pymongo import MongoClient
from flask_socketio import SocketIO
from logging import getLogger

login = LoginManager()
oauth = OAuth()
db = MongoClient()['db']
socketio = SocketIO(logger=getLogger(), engineio_logger=getLogger(), ping_interval=10, ping_timeout=10)
