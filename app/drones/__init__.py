import flask_login
import flask_socketio

from app import log
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


@socketio.on('connect', namespace=message.Namespace.FRONTEND)
def frontend_connect():
    if flask_login.current_user.is_authenticated:
        fac = facilities[str(flask_login.current_user.get()['facility_id'])]
        flask_socketio.join_room(fac.id)
        if fac == home or fac.drone_state != State.IDLE:
            # send data right away
            home.send_heartbeat(drone.battery, drone.pos)
            home.send_drone_state(drone.state)
        return True
    return False
