import flask

from drone import Drone, Status as Dstatus
from mission import Mission, Status as Mstatus
from app import errands

drone_api = flask.Blueprint('drone_api', __name__, url_prefix='/drone_api/')

drone = Drone()
ports = []
errands = []


# drone sends heartbeat every ten seconds, server gives 200 if ok, 299 if mission change, 499 if hard rtl
@drone_api.route('/', methods=['POST'])
def drone_post():

	try:
		# authenticate using the ssl certificate serial
		if drone.serial != flask.request.headers.get('serial'):
			return 'Ungültiger SSL serial', 401

		# update internal drone data
		raw = flask.request.get_json()
		drone.lastUpdate = raw['time']
		drone.coords = (float(raw['coords'][0]), float(raw['coords'][1]))
		drone.status = Dstatus[raw['status']]
		drone.battery = float(raw['battery'])
		drone.stageID = int(raw['stage'])
	except:
		return 'Ungültige Request', 400

	# update drone mission
	mission = errands[0].getStage()
	if drone.status == Dstatus.SITTING and mission.status != Mstatus.STARTING and mission.status != Mstatus.FINISHED:

		# flying / landing > finished
		mission.status = Mstatus.FINISHED
	elif drone.status == Dstatus.FLYING:

		# starting > flying
		if mission.status == Mstatus.STARTING:
			mission.status = Mstatus.FLYING
		elif mission.status == Mstatus.FINISHED:
			pass # we fucked up
	elif drone.status == Dstatus.LANDING:

		# flying > landing
		if mission.status == Mstatus.FLYING:
			mission.status = Mstatus.LANDING
		elif mission.status == Mstatus.FINISHED:
			pass # we fucked up

	# update external mission data
	if missions[0].getStage().id != drone.stageID:
		return Response(missions[0].getStage().getJSON(), 299)

	return 200


# drone sends heartbeat every ten seconds, server gives 200 if ok, 299 if mission change, 499 if hard rtl
@drone_api.route('/', methods=['GET'])
def drone_get():
	pass
