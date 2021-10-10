from enum import Enum
from time import time
from os import environ

import flask_socketio

from app import log
from app.drones import facility
from app.drones.message import ToDrone


class Drone(flask_socketio.Namespace):
	def __init__(self, namespace, home, facilities):
		self.home = home
		self.facilities = facilities
		self.goal_facility = home
		self.latest_facility = home
		self.outbox = None

		# connection to physical drone
		self.lastUpdate = 0
		self.connected = False

		# values from physical drone
		self.pos = (0.0, 0.0)
		self.battery = 0.0
		self.state = State.IDLE

		flask_socketio.Namespace.__init__(self, namespace)

	# generate mission update dictionary to be sent to the drone
	def generate_mission(self, fac, to_home=False):
		return {
			'start': {
				'id': fac.id if to_home else self.home.id,
				'pos': fac.pos if to_home else self.home.pos
			},
			'waypoints': fac.path if to_home else fac.path.reverse(),
			'goal': {
				'id': self.home.id if to_home else fac.id,
				'pos': self.home.pos if to_home else fac.pos
			}
		}

	####################################################################################################################
	# SOCKETIO
	####################################################################################################################

	# if we have a message queued, send it
	def on_connect(self, auth):
		if auth == environ['SUPER_SECRET_DRONE_KEY']:
			self.connected = True
			self.lastUpdate = time()
			if self.outbox:
				self.emit_to_drone(self.outbox[0], self.outbox[1])
			log.info('connected')
		else:
			log.warn('rejected')

	# so long, partner
	def on_disconnect(self):
		self.connected = False
		log.warn('disconnected')

	# we received a heartbeat from the drone; will be registered as a socketio event handler
	def on_heartbeat(self, json_msg):
		self.lastUpdate = time()
		try:
			pos = json_msg['pos']
			battery = json_msg['battery']
		except Exception as e:
			log.warn(e)
			return
		self.pos = pos
		self.battery = battery
		self.goal_facility.send_heartbeat(battery, pos)
		self.latest_facility.send_heartbeat(battery, pos)

	# we received a state update from the drone; will be registered as a socketio event handler
	def on_state_update(self, json_msg):
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
			if content:
				self.emit(msg_type.value, content)
			else:
				self.emit(msg_type.value)
			log.info('sent', (msg_type, content))
		else:
			self.outbox = (msg_type, content)

	####################################################################################################################
	# STATE
	####################################################################################################################

	# we got a state update from the drone; even if drone was returning, goal_facility_id is still the original goal's id
	def state_update(self, state, last_facility_id, goal_facility_id):
		if goal_facility_id != self.goal_facility.id and state != State.UPDATING:
			log.warn("drone's goal facility", goal_facility_id, "not equal to ours:", self.goal_facility.id)
			self.emit_to_drone(ToDrone.EMERGENCY_LAND)
			return

		if state in [State.IDLE]:
			self.latest_facility.set_state(facility.State.IDLE, goal_facility_id)
			if last_facility_id == self.home.id:
				self.goal_facility.set_state(facility.State.IDLE, goal_facility_id)
				if last_facility_id == self.goal_facility.id:
					# unplanned landing after return
					self.goal_facility = self.home
				self.check_for_missions()
			else:
				self.goal_facility.set_state(facility.State.AWAITING_TAKEOFF, goal_facility_id)
				self.goal_facility = self.home
			self.latest_facility = [f for f in self.facilities if f.id == last_facility_id][0]
		elif state in [State.EN_ROUTE, State.LANDING]:
			self.goal_facility.set_state(facility.State.FLYING_TO, goal_facility_id)
			self.latest_facility.set_state(facility.State.FLYING_FROM, goal_facility_id)
		elif state in [State.RETURNING]:
			self.goal_facility.set_state(facility.State.RETURNING_FROM, goal_facility_id)
			self.latest_facility.set_state(facility.State.RETURNING_TO, goal_facility_id)
		elif state in [State.EMERGENCY_LANDING, State.CRASHED]:
			self.goal_facility.set_state(facility.State.EMERGENCY, goal_facility_id)
			self.latest_facility.set_state(facility.State.EMERGENCY, goal_facility_id)

		self.goal_facility.send_drone_state(state)
		self.latest_facility.send_drone_state(state)

	# if we're waiting at home, we can do a new mission
	def check_for_missions(self):
		pending = [f for f in self.facilities if f.drone_requested]
		if len(pending) and self.goal_facility == self.latest_facility == self.home:
			pending.sort(key=lambda f: f.drone_requested_on)
			self.goal_facility = pending[0]
			self.emit_to_drone(ToDrone.UPDATE, self.generate_mission(self.goal_facility))

	####################################################################################################################
	# FRONTEND ORDERS
	####################################################################################################################

	# users from home or the goal can order the drone to emergency land
	def emergency_land(self, user_facility_id):
		if self.goal_facility.id == user_facility_id or user_facility_id == self.home.id:
			self.emit_to_drone(ToDrone.EMERGENCY_LAND)
			return True
		return False

	# users from home or the goal can order the drone to return
	def emergency_return(self, user_facility_id):
		if (self.goal_facility.id == user_facility_id or user_facility_id == self.home.id) and self.latest_facility != self.goal_facility:
			self.emit_to_drone(ToDrone.EMERGENCY_RETURN)
			return True
		return False

	# if the drone is waiting to take off at facility_id, start the mission to home
	def allow_takeoff(self, user_facility_id):
		if user_facility_id == self.latest_facility and self.latest_facility != self.goal_facility:
			self.emit_to_drone(ToDrone.UPDATE, self.generate_mission(self.goal_facility, True))
			return True
		return False

	# request the drone to land on user_facility
	def request(self, user_facility_id):
		user_facility = [f for f in self.facilities if f.id == user_facility_id][0]
		allowed_statees = [facility.State.IDLE, facility.State.FLYING_FROM, facility.State.RETURNING_FROM]
		if user_facility != self.home and user_facility.drone_state in allowed_statees:
			user_facility.set_drone_requested(True)
			self.check_for_missions()
			return True
		return False


# Physical state, i.e. what IS happening; There is NO GUARANTEE that these values are up-to-date
class State(Enum):
	IDLE = 'idle'
	EN_ROUTE = 'en_route'
	LANDING = 'landing'
	RETURNING = 'returning'
	EMERGENCY_LANDING = 'emergency_landing'
	CRASHED = 'crashed'
	UPDATING = 'updating'