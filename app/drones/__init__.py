from flask import current_app

from app.drones.frontend import Frontend
from app.exts import socketio, db
from app.drones.drone import Drone
from app.drones.facility import Facility


facilities = {}
home = None
droneObj = None


# construct facility and drone objects from mongodb entries
def init():
    global home, droneObj

    raw_facilities = db.facilities.find()
    for raw in raw_facilities:
        facilities[str(raw['_id'])] = Facility(str(raw['_id']), raw['pos'], raw['waypoints'], raw['name'], raw['is_home'])
        if raw['is_home']:
            home = facilities[str(raw['_id'])]
    if not home:
        current_app.logger.warning('no home found')

    droneObj = Drone('/drone', home, facilities)

    frontend = Frontend('/frontend', home, facilities, droneObj)
    socketio.on_namespace(frontend)
