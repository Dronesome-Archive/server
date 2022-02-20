import flask
import logging

from app import drones
from app.drones.message import FromDrone
from app.drones.drone import State

# Drone API; Requests: POST; Response: json
drone_api = flask.Blueprint('drone_api', __name__, url_prefix='/drone_api')


# received a message from the drone; authenticated by nginx via mTLS
@drone_api.route('/', methods=['POST'])
def message():
	req = flask.request.json
	logging.info(f'DR_RCV: {req}')
	if req['type'] == FromDrone.HEARTBEAT.value:
		pos = req['pos']
		battery = req['battery']
		drones.droneObj.on_heartbeat(pos, battery)
	elif req['type'] == FromDrone.STATUS_UPDATE.value:
		state = State(req['state'])
		latest_facility_id_str = req['latest_facility_id']
		goal_facility_id_str = req['goal_facility_id']
		if latest_facility_id_str and goal_facility_id_str:
			drones.droneObj.on_state_update(state, latest_facility_id_str, goal_facility_id_str)
		else:
			# the drone has no latest/goal facilities when just starting up
			drones.droneObj.on_state_update(state, drones.home.id_str, drones.home.id_str)
	else:
		logging.warning(f"DR_RCV: unknown type")
	rep = reply()
	logging.info(f"DR_SND: {rep}")
	return rep

# messages are answered with an order from us or just an empty order
def reply():
	if drones.droneObj.outbox:
		msg = drones.droneObj.outbox
		drones.droneObj.outbox = None
	else:
		msg = { 'type': None }
	return msg
