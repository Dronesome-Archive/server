from enum import Enum
from time import time
from geopy import distance

class Drone:
	def __init__(self, serial):
		self.serial = serial
		self.lastUpdate = 0
		self.coords = (0.0, 0,0)
		self.status = Status.SITTING
		self.battery = 0.0
		self.stageID = 0
		
	
class Status(Enum):
	FLYING = 'FLYING'
	LANDING = 'LANDING'
	SITTING = 'SITTING'
	

