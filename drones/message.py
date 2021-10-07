from enum import Enum


class ToDrone(Enum):
    UPDATE = 'update'
    RETURN = 'return'
    EMERGENCY_LAND = 'emergency_land'


class FromDrone(Enum):
    HEARTBEAT = 'heartbeat'
    STATUS_UPDATE = 'status_update'


class ToFrontend(Enum):
    FACILITY_DRONE_STATUS = 'facility_drone_status'
    DRONE_STATUS = 'drone_status'
    HEARTBEAT = 'heartbeat'
    DRONE_REQUESTED = 'drone_requested'


class Namespace(Enum):
    FRONTEND = 'frontend'
    DRONE = 'drone'
