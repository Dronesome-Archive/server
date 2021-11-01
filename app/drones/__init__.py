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

    print('facilities initialized')


@socketio.on('connect', namespace=message.Namespace.FRONTEND)
def frontend_connect():
    log.info('FRONTEND CONNECT')
    if flask_login.current_user.is_authenticated:
        log.info('AUTHENTICATED')
        fac = facilities[str(flask_login.current_user.get()['facility_id'])]
        flask_socketio.join_room(fac.id)
        fac.send_state()
        if fac == home or fac.state != State.IDLE:
            # send drone data right away
            fac.send(message.ToFrontend.FACILITY_STATE)
            fac.send(message.ToFrontend.DRONE_REQUESTED)
            fac.send(message.ToFrontend.HEARTBEAT, battery=drone.battery, pos=drone.pos)
            fac.send(message.ToFrontend.DRONE_STATE, state=drone.state)
        return True
    return False


@socketio.on('message', namespace=message.Namespace.FRONTEND)
def test_message(msg):
    log.info('FRONTEND MESSAGE')  # TODO: how to even receive messages correctly?
    print('FRONTEND MESSAGE')
    print(msg)
