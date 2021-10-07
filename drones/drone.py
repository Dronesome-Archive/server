from enum import Enum
from time import time

import flask_socketio
from flask import current_app

from drones import home, facilities
import log
from message import ToDrone, Namespace
import facility


class Drone(flask_socketio.Namespace):
	def __init__(self, namespace, serial):
		self.serial = serial
		self.goal_facility = home
		self.latest_facility = home
		self.outbox = None

		# connection to physical drone
		self.lastUpdate = 0
		self.connected = False

		# values from physical drone
		self.pos = (0.0, 0.0)
		self.battery = 0.0
		self.status = Status.IDLE

		flask_socketio.Namespace.__init__(self, namespace)

	####################################################################################################################
	# SOCKETIO
	####################################################################################################################

	# if we have a message queued, send it
	def on_connect(self, auth):
		if auth == current_app.config['SUPER_SECRET_DRONE_KEY']:
			self.connected = True
			self.lastUpdate = time()
			if self.outbox:
				self.send(self.outbox[0], self.outbox[1])
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

	# we received a status update from the drone; will be registered as a socketio event handler
	def on_status_update(self, json_msg):
		self.lastUpdate = time()
		try:
			status = Status(json_msg['status'])
			latest_facility_id = json_msg['latest_facility_id']
			goal_facility_id = json_msg['goal_facility_id']
		except Exception as e:
			log.warn(e)
			return
		self.status_update(status, latest_facility_id, goal_facility_id)

	# emit message to drone if connected, else queue in outbox
	def send(self, msg_type, content=None):
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

	# we got a status update from the drone; even if drone was returning, goal_facility_id is still the original goal's id
	def status_update(self, status, last_facility_id, goal_facility_id):
		if goal_facility_id != self.goal_facility.id and status != Status.UPDATING:
			log.warn("drone's goal facility", goal_facility_id, "not equal to ours:", self.goal_facility.id)
			self.send(ToDrone.EMERGENCY_LAND)
			return

		if status in [Status.IDLE]:
			self.latest_facility.set_status(facility.Status.IDLE, goal_facility_id)
			if last_facility_id == home.id:
				self.goal_facility.set_status(facility.Status.IDLE, goal_facility_id)
				if last_facility_id == self.goal_facility.id:
					# unplanned landing after return
					self.goal_facility = home
				self.check_for_missions()
			else:
				self.goal_facility.set_status(facility.Status.AWAITING_TAKEOFF, goal_facility_id)
				self.goal_facility = home
			self.latest_facility = [f for f in facilities if f.id == last_facility_id][0]
		elif status in [Status.EN_ROUTE, Status.LANDING]:
			self.goal_facility.set_status(facility.Status.FLYING_TO, goal_facility_id)
			self.latest_facility.set_status(facility.Status.FLYING_FROM, goal_facility_id)
		elif status in [Status.RETURNING]:
			self.goal_facility.set_status(facility.Status.RETURNING_FROM, goal_facility_id)
			self.latest_facility.set_status(facility.Status.RETURNING_TO, goal_facility_id)
		elif status in [Status.EMERGENCY_LANDING, Status.CRASHED]:
			self.goal_facility.set_status(facility.Status.EMERGENCY, goal_facility_id)
			self.latest_facility.set_status(facility.Status.EMERGENCY, goal_facility_id)

		self.goal_facility.send_drone_status(status)
		self.latest_facility.send_drone_status(status)

	# if we're waiting at home, we can do a new mission
	def check_for_missions(self):
		pending = [f for f in facilities if f.drone_requested]
		if len(pending) and self.goal_facility == self.latest_facility == home:
			pending.sort(key=lambda f: f.drone_requested_on)
			self.goal_facility = pending[0]
			self.send(ToDrone.UPDATE, self.goal_facility.generate_mission())

	####################################################################################################################
	# FRONTEND ORDERS
	####################################################################################################################

	# users from home or the goal can order the drone to emergency land
	def emergency_land(self, user_facility_id):
		if self.goal_facility.id == user_facility_id or user_facility_id == home.id:
			self.send(ToDrone.EMERGENCY_LAND)

	# users from home or the goal can order the drone to return
	def return_to_last(self, user_facility_id):
		if (self.goal_facility.id == user_facility_id or user_facility_id == home.id) and self.latest_facility != self.goal_facility:
			self.send(ToDrone.RETURN)

	# if the drone is waiting to take off at facility_id, start the mission to home
	def allow_takeoff(self, user_facility_id):
		if user_facility_id == self.latest_facility and self.latest_facility != self.goal_facility:
			self.send(ToDrone.UPDATE, self.goal_facility.generate_mission(True))


# Physical status, i.e. what IS happening; There is NO GUARANTEE that these values are up-to-date
class Status(Enum):
	IDLE = 'idle'
	EN_ROUTE = 'en_route'
	LANDING = 'landing'
	RETURNING = 'returning'
	EMERGENCY_LANDING = 'emergency_landing'
	CRASHED = 'crashed'
	UPDATING = 'updating'
