import time
from enum import Enum

from app import log
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
        self.drone_goal = self

    # we have a new state, relay to our facility
    def set_state(self, state, goal_facility):
        if self.state != state or self.drone_goal != goal_facility:
            self.state = state
            self.drone_goal = goal_facility
            if state != State.IDLE:
                self.set_drone_requested(False)
            self.send(ToFrontend.FACILITY_STATE)

    # set drone request state and send to frontend
    def set_drone_requested(self, drone_requested):
        if self.drone_requested != drone_requested:
            if drone_requested:
                self.drone_requested_on = time.time()
            self.drone_requested = drone_requested
            self.send(ToFrontend.DRONE_REQUESTED)

    # send a socketio message to the frontend
    def send(self, msg_type, **kwargs):
        if msg_type == ToFrontend.FACILITY_STATE:
            content = {'state': self.state.value, 'goal_id': self.drone_goal.id}
        elif msg_type == ToFrontend.DRONE_REQUESTED:
            content = {'requested': self.drone_requested}
        elif msg_type == ToFrontend.DRONE_STATE:
            content = {'state': kwargs['state'].value}
        elif msg_type == ToFrontend.HEARTBEAT:
            content = {'pos': kwargs['pos'], 'battery': kwargs['battery']}
        log.info(msg_type.value, content)
        socketio.emit(msg_type.value, content, namespace='/'+Namespace.FRONTEND.value, to=self.id)


# state of the drone in relation to our facility
class State(Enum):
    IDLE = 'idle'
    AWAITING_TAKEOFF = 'awaiting_takeoff'
    EN_ROUTE = 'en_route'
    RETURNING = 'returning'
    EMERGENCY = 'emergency'
