import time
from enum import Enum

from app.exts import socketio
from app.drones.message import Namespace, ToFrontend


# landing pad the users of which can request the drone
class Facility:
    def __init__(self, facility_id, pos, waypoints, name, is_home):
        self.id = facility_id
        self.pos = pos
        self.waypoints = waypoints  # in-between-waypoints from the facility to home
        self.name = name
        self.is_home = is_home
        self.drone_state = State.IDLE
        self.drone_requested = False
        self.drone_requested_on = time.time()

    # the drone has new heartbeat data, relay to our facility
    def send_heartbeat(self, battery, pos):
        print(ToFrontend.HEARTBEAT.value, battery, pos)
        socketio.emit(
            ToFrontend.HEARTBEAT.value,
            {'battery': battery, 'pos': pos},
            namespace=Namespace.FRONTEND.value,
            to=self.id
        )

    # the drone has a new internal state, relay to our facility
    def send_drone_state(self, state):
        print(ToFrontend.DRONE_STATUS.value, state)
        socketio.emit(
            ToFrontend.DRONE_STATUS.value,
            {'state': state.value},
            namespace=Namespace.FRONTEND.value,
            to=self.id
        )

    # we have a new state, relay to our facility
    def set_state(self, state, goal_id):
        if self.drone_state != state:
            self.drone_state = state
            if state != State.IDLE:
                self.set_drone_requested(False)
            print(ToFrontend.FACILITY_DRONE_STATUS.value, state, goal_id)
            socketio.emit(
                ToFrontend.FACILITY_DRONE_STATUS.value,
                {'state': state.value, 'goal_id': goal_id},
                namespace=Namespace.FRONTEND.value,
                to=self.id
            )

    # set drone request state and send to frontend
    def set_drone_requested(self, drone_requested):
        if not self.drone_requested == drone_requested:
            if drone_requested:
                self.drone_requested_on = time.time()
            self.drone_requested = drone_requested
            print(ToFrontend.DRONE_REQUESTED.value, drone_requested)
            socketio.emit(
                ToFrontend.DRONE_REQUESTED.value,
                {'requested': drone_requested},
                namespace=Namespace.FRONTEND.value,
                to=self.id
            )


# state of the drone in relation to our facility
class State(Enum):
    IDLE = 'idle'
    AWAITING_TAKEOFF = 'awaiting_takeoff'
    FLYING_TO = 'flying_to'
    RETURNING_TO = 'returning_to'
    FLYING_FROM = 'flying_from'
    RETURNING_FROM = 'returning_from'
    EMERGENCY = 'emergency'
