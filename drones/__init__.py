import flask_login
import flask_socketio
from flask import current_app

from drone import Drone
from exts import socketio, db
from facility import Facility
import log
import message

raw_facilities = db.facilities.find()
facilities = []
home = None
for raw in raw_facilities:
    facilities.append(Facility(raw['_id'], raw['pos'], raw['path'], raw['name']))
    if raw['is_home']:
        home = facilities[-1]
if not home:
    log.warn('no home found')

drone = Drone('/drone', current_app.config['DRONE_SERIAL'])
socketio.on_namespace(drone)


@socketio.on('connect', namespace=message.Namespace.FRONTEND)
def frontend_connect():
    if flask_login.current_user.is_authenticated:
        facility_id = flask_login.current_user.get()['facility_id']
        flask_socketio.join_room(facility_id)
        if facility_id == home.id:
            # send data right away
            home.send_heartbeat(drone.battery, drone.pos)
            home.send_drone_status(drone.status)
        return True
    return False
