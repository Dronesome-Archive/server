import time
from enum import Enum

from app.exts import socketio
from app.drones import home, drone
from app.drones.message import Namespace, ToFrontend


# landing pad the users of which can request the drone
class Facility:
    def __init__(self, facility_id, pos, path, name):
        self.id = facility_id
        self.pos = pos
        self.path = path
        self.name = name
        self.drone_status = Status.AWAITING_REQUEST
        self.drone_requested = False
        self.drone_requested_on = time.time()

    # the drone has new heartbeat data, relay to our facility
    def send_heartbeat(self, battery, pos):
        socketio.emit(
            ToFrontend.HEARTBEAT.value,
            {'battery': battery, 'pos': pos},
            namespace=Namespace.FRONTEND.value,
            to=self.id
        )

    # the drone has a new internal status, relay to our facility
    def send_drone_status(self, status):
        socketio.emit(
            ToFrontend.DRONE_STATUS.value,
            status.value,
            namespace=Namespace.FRONTEND.value,
            to=self.id
        )

    # the drone has a new status, relay to our facility
    def set_status(self, status, goal_id):
        if self.drone_status != status:
            self.drone_status = status
            if status != Status.IDLE:
                self.set_drone_requested(False)
            socketio.emit(
                ToFrontend.FACILITY_DRONE_STATUS.value,
                {'status': status.value, 'goal_id': goal_id},
                namespace=Namespace.FRONTEND.value,
                to=self.id
            )

    # set drone request status and send to frontend
    def set_drone_requested(self, drone_requested):
        if not self.drone_requested == drone_requested:
            if drone_requested:
                self.drone_requested_on = time.time()
            self.drone_requested = drone_requested
            socketio.emit(
                ToFrontend.DRONE_REQUESTED.value,
                self.drone_requested,
                namespace=Namespace.FRONTEND.value,
                to=self.id
            )

    # a user with the right auth has requested a drone
    def request_drone(self):
        if self == home:
            return False, "Der Kurier kann nicht von der Basis aus bestellt werden."
        elif self.drone_status == Status.AWAITING_TAKEOFF:
            return False, "Der Kurier ist bereits anwesend, bitte geben sie die Starterlaubnis."
        elif self.drone_status in [Status.FLYING_TO, Status.RETURNING_TO]:
            return False, "Der Kurier ist bereits auf dem Weg."
        elif self.drone_status == Status.EMERGENCY:
            return False, "Der Kurier is Notgelandet und muss gewartet werden."
        else:
            self.set_drone_requested(True)
            # check for missions anyway, just in case the message to the drone wasn't received
            drone.check_for_missions()
            return True, "Kurier angefordert."

    # generate mission update dictionary to be sent to the drone
    def generate_mission(self, to_home=False):
        return {
            'start': {
                'id': self.id if to_home else home.id,
                'pos': self.pos if to_home else home.pos
            },
            'path': self.path if to_home else self.path.reverse(),
            'goal': {
                'id': home.id if to_home else self.id,
                'pos': home.pos if to_home else self.pos
            }
        }


# status of the drone in relation to our facility
class Status(Enum):
    IDLE = 'idle'
    AWAITING_TAKEOFF = 'awaiting_takeoff'
    FLYING_TO = 'flying_to'
    RETURNING_TO = 'returning_to'
    FLYING_FROM = 'flying_from'
    RETURNING_FROM = 'returning_from'
    EMERGENCY = 'emergency'
