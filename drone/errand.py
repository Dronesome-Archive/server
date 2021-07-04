import mission

# Multiple missions to be done in succession
class Errand:
	def __init__(self, port):
		self.missions = []
		self.currentMission = 0
	
	# Get current mission
	def getStage(self):
		return self.missions[self.currentMission]

	