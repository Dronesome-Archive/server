from enum import Enum


# Virtual representation of the drone that is ONLY updated by the drone's heartbeat
class Drone:
	def __init__(self, serial):
		self.serial = serial
		self.lastUpdate = 0
		self.coords = (0.0, 0.0)
		self.status = Status.SITTING
		self.battery = 0.0
		self.stageID = 0


# Physical status, i.e. what IS happening
class Status(Enum):
	FLYING = 'FLYING'  # regular flight
	LANDING = 'LANDING'  # raspi is directly controlling the landing
	SITTING = 'SITTING'  # not in air
	
