from enum import Enum
from geographiclib.geodesic import Geodesic


# Single flight from takeoff to landing on a port
class Mission:
	def __init__(self, goal, waypoints):
		self.goal = goal
		self.waypoints = waypoints
		self.status = Status.STARTING


# Logical status, i.e. what SHOULD BE happening
class Status(Enum):
	STARTING = 0
	FLYING = 1  #
	LANDING = 2
	FINISHED = 3
