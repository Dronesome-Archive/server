from app.blueprints.auth import auth
from app.blueprints.drone_control import drone_control
from app.blueprints.drone_api import drone_api
from app.blueprints.pages import pages
from app.blueprints.users import users

blueprints = [auth, drone_control, drone_api, pages, users]
