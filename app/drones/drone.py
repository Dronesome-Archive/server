from enum import Enum
from time import time
from os import environ

import flask_socketio

from app import log
from app.drones import facility
from app.drones.message import ToDrone, ToFrontend


class Drone(flask_socketio.Namespace):
	def __init__(self, namespace, home, facilities):
		# facilities
		self.home = home
		self.facilities = facilities
		self.goal_facility = home
		self.latest_facility = home
		for f in self.facilities.values():
			f.set_state(facility.State.IDLE, self.goal_facility)

		# connection to physical drone
		self.lastUpdate = 0
		self.connected = False
		self.outbox = None

		# values from physical drone
		self.pos = (0.0, 0.0)
		self.battery = 0.0
		self.state = State.IDLE

		flask_socketio.Namespace.__init__(self, namespace)

	# generate mission update dictionary to be sent to the drone
	def generate_mission(self, start, goal):
		return {
			'start': {
				'id': start.id_str,
				'pos': start.pos
			},
			'waypoints': start.waypoints if goal == self.home else goal.waypoints[::-1],
			'goal': {
				'id': start.id_str,
				'pos': start.pos
			}
		}

	####################################################################################################################
	# SOCKETIO
	####################################################################################################################

	# if we have a message queued, send it
	def on_connect(self, auth):
		if str(auth) == environ['SUPER_SECRET_DRONE_KEY']:
			log.info('DR_CON')
			self.connected = True
			self.lastUpdate = time()
			if self.outbox:
				self.emit_to_drone(self.outbox[0], self.outbox[1])
		else:
			log.warn('DR_REJ')

	# so long, partner
	def on_disconnect(self):
		self.connected = False
		log.warn('FE_DIS')

	# we received a heartbeat from the drone; will be registered as a socketio event handler
	def on_heartbeat(self, json_msg):
		log.info('DR_RCV: heartbeat', json_msg)
		self.lastUpdate = time()
		try:
			pos = json_msg['pos']
			battery = json_msg['battery']
		except Exception as e:
			log.warn(e)
			return
		self.pos = pos
		self.battery = battery
		self.goal_facility.send(ToFrontend.HEARTBEAT, **json_msg)
		self.latest_facility.send(ToFrontend.HEARTBEAT, **json_msg)

	# we received a state update from the drone; will be registered as a socketio event handler
	def on_state_update(self, json_msg):
		log.info('DR_RCV: state_update', json_msg)
		self.lastUpdate = time()
		try:
			state = State(json_msg['state'])
			latest_facility_id = json_msg['latest_facility_id']
			goal_facility_id = json_msg['goal_facility_id']
		except Exception as e:
			log.warn(e)
			return
		self.state_update(state, latest_facility_id, goal_facility_id)

	# emit message to drone if connected, else queue in outbox
	def emit_to_drone(self, msg_type, content=None):
		if self.connected:
			log.info('DR_SND: ', msg_type.value)
			if content:
				log.info(content)
				self.emit(msg_type.value, content)
			else:
				self.emit(msg_type.value)
		else:
			log.info('DR_QUE: ', msg_type.value)
			self.outbox = (msg_type, content)

	####################################################################################################################
	# STATE
	####################################################################################################################

	# we got a state update from the drone; even if drone was returning, goal_facility_id is still the original goal's id
	def state_update(self, state, current_facility_id_str, goal_facility_id_str):
		current_facility = self.facilities[current_facility_id_str]
		goal_facility = self.facilities[goal_facility_id_str]
		if goal_facility != self.goal_facility and state != State.UPDATING:
			log.warn("drone's goal facility", goal_facility.id_str, "not equal to ours:", self.goal_facility.id_str)
			self.goal_facility = goal_facility

		if state in [State.IDLE]:
			self.goal_facility = self.home
			if current_facility == self.home:
				# landed on home, errand complete
				self.latest_facility.set_state(facility.State.IDLE, self.goal_facility)
				self.goal_facility.set_state(facility.State.IDLE, self.goal_facility)
			else:
				# landed on non-home
				self.latest_facility.set_state(facility.State.AWAITING_TAKEOFF, self.goal_facility)
				self.goal_facility.set_state(facility.State.AWAITING_TAKEOFF, self.goal_facility)
		elif state in [State.EN_ROUTE, State.LANDING]:
			self.latest_facility.set_state(facility.State.EN_ROUTE, self.goal_facility)
			self.goal_facility.set_state(facility.State.EN_ROUTE, self.goal_facility)
		elif state in [State.EMERGENCY_RETURNING, State.RETURN_LANDING]:
			self.latest_facility.set_state(facility.State.RETURNING, self.goal_facility)
			self.goal_facility.set_state(facility.State.RETURNING, self.goal_facility)
		elif state in [State.EMERGENCY_LANDING, State.CRASHED]:
			self.latest_facility.set_state(facility.State.EMERGENCY, self.goal_facility)
			self.goal_facility.set_state(facility.State.EMERGENCY, self.goal_facility)

		self.latest_facility = current_facility
		self.goal_facility.send_drone_state(state)
		self.latest_facility.send_drone_state(state)

	# if we're waiting at home, we can do a new mission
	def check_for_missions(self):
		log.info('checking for missions...')
		pending = [fac for fac_id, fac in self.facilities.items() if fac.drone_requested]
		log.info(pending)
		if len(pending) and self.goal_facility == self.latest_facility == self.home:
			pending.sort(key=lambda f: f.drone_requested_on)
			self.goal_facility = pending[0]
			self.latest_facility.set_state(facility.State.AWAITING_TAKEOFF, self.goal_facility)
			self.goal_facility.set_state(facility.State.AWAITING_TAKEOFF, self.goal_facility)

	####################################################################################################################
	# FRONTEND ORDERS
	####################################################################################################################

	# users from home or the goal can order the drone to emergency land
	def emergency_land(self, user_facility_id_str):
		log.info('FE_RCV: emergency_land', user_facility_id_str)
		if user_facility_id_str in [self.goal_facility.id_str, self.latest_facility.id_str, self.home.id_str]:
			self.emit_to_drone(ToDrone.EMERGENCY_LAND)
			return True
		log.warn('emergency_land denied')
		return False

	# users from home or the goal can order the drone to return
	def emergency_return(self, user_facility_id_str):
		log.info('FE_RCV: emergency_return', user_facility_id_str)
		if user_facility_id_str in [self.goal_facility.id_str, self.latest_facility.id_str, self.home.id_str]:
			self.emit_to_drone(ToDrone.EMERGENCY_RETURN)
			return True
		log.warn('emergency_return denied')
		return False

	# if the drone is waiting to take off at facility_id, start the mission to home
	def allow_takeoff(self, user_facility_id_str):
		log.info('FE_RCV: allow_takeoff', user_facility_id_str)
		if user_facility_id_str == self.latest_facility.id_str and self.latest_facility.state == facility.State.AWAITING_TAKEOFF:
			self.emit_to_drone(ToDrone.UPDATE, self.generate_mission(self.latest_facility, self.goal_facility))
			return True
		log.warn('allow_takeoff denied')
		return False

	# request the drone to land on user_facility
	def request(self, user_facility_id_str):
		log.info('FE_RCV: request', user_facility_id_str)
		fac = self.facilities[user_facility_id_str]
		idle = (fac.state == facility.State.IDLE and fac.drone_goal != fac)
		en_route = (fac.state == facility.State.EN_ROUTE and fac.drone_goal != fac)
		returning = (fac.state == facility.State.RETURNING and fac.drone_goal == fac)
		if fac != self.home and (idle or en_route or returning):
			fac.set_drone_requested(True)
			self.check_for_missions()
			return True
		log.warn('request denied')
		return False


# Physical state, i.e. what IS happening; There is NO GUARANTEE that these values are up-to-date
class State(Enum):
	IDLE = 'idle'
	EN_ROUTE = 'en_route'
	LANDING = 'landing'
	RETURN_LANDING = 'return_landing'
	EMERGENCY_RETURNING = 'emergency_returning'
	EMERGENCY_LANDING = 'emergency_landing'
	CRASHED = 'crashed'
	UPDATING = 'updating'
