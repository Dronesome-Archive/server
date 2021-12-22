import flask_login
import flask_socketio

from app import log
from app.drones.frontend import Frontend
from app.exts import socketio, db
from app.drones import message
from app.drones.drone import Drone
from app.drones.facility import Facility, State


facilities = {}
home = None
drone = None


def init():
    global home, drone

    raw_facilities = db.facilities.find()
    for raw in raw_facilities:
        facilities[str(raw['_id'])] = Facility(str(raw['_id']), raw['pos'], raw['waypoints'], raw['name'], raw['is_home'])
        if raw['is_home']:
            home = facilities[str(raw['_id'])]
    if not home:
        log.warn('no home found')

    drone = Drone('/drone', home, facilities)
    socketio.on_namespace(drone)

    frontend = Frontend('/frontend', home, facilities, drone)
    socketio.on_namespace(frontend)

    print('facilities initialized')
