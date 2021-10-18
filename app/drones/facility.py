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
        self.state = State.IDLE
        self.drone_requested = False
        self.drone_requested_on = time.time()

    # the drone has a new goal, relay to our facility
    def send_goal(self, goal_facility):
        print(ToFrontend.DRONE_GOAL.value, str(goal_facility.id))
        socketio.emit(
            ToFrontend.DRONE_GOAL.value,
            {'goal_facility_id': str(goal_facility.id)},
            namespace=Namespace.FRONTEND.value,
            to=self.id
        )

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
        print(ToFrontend.DRONE_STATE.value, state)
        socketio.emit(
            ToFrontend.DRONE_STATE.value,
            {'state': state.value},
            namespace=Namespace.FRONTEND.value,
            to=self.id
        )

    # send our own state
    def send_state(self):
        print(ToFrontend.FACILITY_STATE.value, self.state.value)
        socketio.emit(
            ToFrontend.FACILITY_STATE.value,
            {'state': self.state.value},
            namespace=Namespace.FRONTEND.value,
            to=self.id
        )

    # we have a new state, relay to our facility
    def set_state(self, state):
        if self.state != state:
            self.state = state
            if state != State.IDLE:
                self.set_drone_requested(False)
            print(ToFrontend.FACILITY_STATE.value, state)
            self.send_state()

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
