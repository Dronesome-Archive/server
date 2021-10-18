from enum import Enum


class ToDrone(Enum):
    UPDATE = 'update'
    EMERGENCY_RETURN = 'emergency_return'
    EMERGENCY_LAND = 'emergency_land'


class FromDrone(Enum):
    HEARTBEAT = 'heartbeat'
    STATUS_UPDATE = 'state_update'


class ToFrontend(Enum):
    DRONE_GOAL = 'drone_goal'
    FACILITY_STATE = 'facility_state'
    DRONE_STATE = 'drone_state'
    HEARTBEAT = 'heartbeat'
    DRONE_REQUESTED = 'drone_requested'


class Namespace(Enum):
    FRONTEND = 'frontend'
    DRONE = 'drone'
