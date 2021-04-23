from enum import Enum
from geographiclib.geodesic import Geodesic

class Status(Enum):
	STARTING = 0
	FLYING = 1
	LANDING = 2
	FINISHED = 3

# Single flight from takeoff to landing on a port
class Mission:
	def __init__(self, goal, waypoints, geofence):
		self.goal = goal
		self.waypoints = waypoints
		self.geofence = geofence
		self.status = Status.STARTING

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