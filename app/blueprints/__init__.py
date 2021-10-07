from app.blueprints.auth import auth
from app.blueprints.drone_control import drone_control
from app.blueprints.pages import pages
from app.blueprints.users import users

blueprints = [auth, drone_control, pages, users]
