import stage

# Multiple stages to be done in succession
class Errand:
	def __init__(self, port):
		self.stages = []
		self.currentStage = 0
	
	# Get current stage
	def getStage():
		return self.stages[self.currentStage]

	