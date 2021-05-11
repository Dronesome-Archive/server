from enum import Enum
from geographiclib.geodesic import Geodesic

# Single flight from takeoff to landing on a port
class Mission:
	def __init__(self, goal, waypoints, geofence):
		self.goal = goal
		self.waypoints = waypoints
		self.geofence = geofence
		self.status = Status.STARTING

	# Return soft geofence, where drone shouldn't go but won't RTL either
	def getGeofence():
		if status == Status.FLYING:
			return self.geofence
		else:
			return [
				geod.Direct(self.goal.coords, 0, 10),
				geod.Direct(self.goal.coords, 90, 10),
				geod.Direct(self.goal.coords, 180, 10),
				geod.Direct(self.goal.coords, 270, 10)
			]

# Logical status, i.e. what SHOULD BE happening
class Status(Enum):
	STARTING = 0
	FLYING = 1
	LANDING = 2
	FINISHED = 3