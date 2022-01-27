import flask
import logging

from app import drones
from app.drones.message import FromDrone
from app.drones.drone import State

# Drone API; Requests: POST; Response: json
drone_api = flask.Blueprint('drone_api', __name__, url_prefix='/drone_api')


# received a message from the drone; authenticated by nginx via mTLS
@drone_api.route('/<string:msg_type>', methods=['POST'])
def message(msg_type):
	if msg_type == FromDrone.HEARTBEAT.value:
		logging.info('DR_RCV: heartbeat')
		try:
			pos = flask.request.json['pos']
			battery = flask.request.json['battery']
		except Exception as e:
			logging.warning(e)
			return reply()
		drones.droneObj.on_heartbeat(pos, battery)
	elif msg_type == FromDrone.STATUS_UPDATE.value:
		logging.info('DR_RCV: status update')
		try:
			state = State(flask.request.json['state'])
			latest_facility_id_str = flask.request.json['latest_facility_id']
			goal_facility_id_str = flask.request.json['goal_facility_id']
		except Exception as e:
			logging.warning(e)
			return reply()
		if latest_facility_id_str and goal_facility_id_str:
			drones.droneObj.on_state_update(state, latest_facility_id_str, goal_facility_id_str)
		else:
			# the drone has no latest/goal facilities when just starting up
			drones.droneObj.on_state_update(state, drones.home.id_str, drones.home.id_str)
	else:
		logging.warning(f'DR_RCV: unknown type {msg_type}')
	return reply()

# messages are answered with an order from us or just an empty order
def reply():
	if drones.droneObj.outbox:
		msg = drones.droneObj.outbox
		drones.droneObj.outbox = None
	else:
		msg = { 'type': None }
	return msg
