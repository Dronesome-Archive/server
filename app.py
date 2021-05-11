from flask import Flask
from flask import request
from flask import Response
from geopy import distance

import mission
import drone 

app = Flask(__name__)

testlist=[1,2,3]
test=distance.distance()

drone = []
ports = []
missions = []

@app.route('/')
def hello_world():
	return 'whats good bitch'

@app.route('/test')
def ayy():
	return 'mask of percucets'

@app.route('/approve')
def approve():
	port = None
	if missions[0].stage().goal == port and missions[0].stage().status == mission.Status.FINISHED:
		missions[0].currentStage += 1


# drone sends heartbeat every ten seconds, server gives 200 if ok, 299 if mission change, 499 if hard rtl
@app.route('/drone', methods=['POST'])
def drone():

	try:
		# authenticate using the ssl certificate serial
		if drone.serial != request.headers.get('serial') return 401

		# update internal drone data
		raw = request.get_json()
		drone.lastUpdate = raw['time']
		drone.coords = (float(raw['coords'][0]), float(raw['coords'][1]))
		drone.status = Drone.Status[raw['status']]
		drone.battery = float(raw['battery'])
		drone.stageID = int(raw['stage'])
	except:
		return 400

	# update drone mission
	if drone.status == Drone.Status.SITTING and missions[0].getStage().status != mission.Status.STARTING and missions[0].getStage().status != mission.Status.FINISHED:
		
		# flying / landing > finished
		missions[0].getStage().status == mission.Status.FINISHED
	elif drone.status == Drone.Status.FLYING:
		
		# starting > flying
		if missions[0].getStage().status == mission.Status.STARTING:
			missions[0].getStage().status == mission.Status.FLYING
		elif missions[0].getStage().status == mission.Status.FINISHED:
			pass # we fucked up
	elif drone.status == Drone.Status.LANDING:
		
		# flying > landing
		if missions[0].getStage().status == mission.Status.FLYING:
			missions[0].getStage().status == mission.Status.LANDING
		elif missions[0].getStage().status == mission.Status.FINISHED:
			pass # we fucked up
	
	# update external mission data
	if missions[0].getStage().id != drone.stageID:
		return Response(missions[0].getStage().getJSON(), 299)
	
	return 200

