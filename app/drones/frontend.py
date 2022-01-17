import flask_socketio
import flask_login

from app import log
from app.drones import message
from app.drones.facility import State


class Frontend(flask_socketio.Namespace):
    def __init__(self, namespace, home, facilities, drone):
        self.home = home
        self.facilities = facilities
        self.drone = drone
        flask_socketio.Namespace.__init__(self, namespace)
    
    def on_connect(self):
        log.info('FE_CON')
        #if flask_login.current_user.is_authenticated:
        if True:
            #fac = self.facilities[str(flask_login.current_user.get()['facility_id'])]
            fac = self.home
            flask_socketio.join_room(fac.id_str)
            fac.send(message.ToFrontend.FACILITY_STATE)
            if fac == self.home or fac.state != State.IDLE:
                # send drone data right away
                fac.send(message.ToFrontend.DRONE_REQUESTED)
                fac.send(message.ToFrontend.HEARTBEAT, battery=self.drone.battery, pos=self.drone.pos)
                fac.send(message.ToFrontend.DRONE_STATE, state=self.drone.state)
            return True
        log.warn('FE_REJ')
        return False
