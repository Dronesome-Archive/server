import logging
from enum import Enum

from app.drones import facility
from app.drones.message import ToDrone, ToFrontend


class Drone:
	def __init__(self, namespace, home, facilities):
		# facilities
		self.home = home
		self.facilities = facilities
		self.goal_facility = home
		self.latest_facility = home
		for f in self.facilities.values():
			f.set_state(facility.State.IDLE, self.goal_facility)

		# connection to physical drone
		self.outbox = None

		# values from physical drone
		self.pos = (0.0, 0.0)
		self.battery = 0.0
		self.state = State.IDLE

	# generate mission update dictionary to be sent to the drone
	def generate_update(self, start, goal):
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

	# put a message into self.outbox
	def queue_message(self, msg_type, content={}):
		self.outbox = content
		self.outbox['type'] = msg_type.val

	# if we're waiting at home, we can do a new mission
	def check_for_missions(self):
		pending = [fac for fac_id, fac in self.facilities.items() if fac.drone_requested]
		logging.info(f'Found pending missions: {pending}')
		if len(pending) and self.goal_facility == self.latest_facility == self.home:
			pending.sort(key=lambda f: f.drone_requested_on)
			self.goal_facility = pending[0]
			self.latest_facility.set_state(facility.State.AWAITING_TAKEOFF, self.goal_facility)
			self.goal_facility.set_state(facility.State.AWAITING_TAKEOFF, self.goal_facility)


	####################################################################################################################
	# ORDERS FROM COMPANION
	####################################################################################################################

	# we received a heartbeat from the drone
	def on_heartbeat(self, pos, battery):
		self.pos = pos
		self.battery = battery
		self.goal_facility.send(ToFrontend.HEARTBEAT, {'position': pos, 'battery': battery})
		self.latest_facility.send(ToFrontend.HEARTBEAT, {'position': pos, 'battery': battery})

	# we got a state update from the drone; even if drone was returning, goal_facility_id is still the original goal's id
	def on_state_update(self, state, current_facility_id_str, goal_facility_id_str):
		current_facility = self.facilities[current_facility_id_str]
		goal_facility = self.facilities[goal_facility_id_str]
		if goal_facility != self.goal_facility and state != State.UPDATING:
			logging.warn(f"drone's goal facility {goal_facility.id_str} not equal to ours: {self.goal_facility.id_str}")
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


	####################################################################################################################
	# ORDERS FROM FRONTEND
	####################################################################################################################

	# users from home or the goal can order the drone to emergency land
	def emergency_land(self, user_facility_id_str):
		logging.info(f'FE_RCV: emergency_land from {user_facility_id_str}')
		if user_facility_id_str in [self.goal_facility.id_str, self.latest_facility.id_str, self.home.id_str]:
			self.queue_message(ToDrone.EMERGENCY_LAND)
			return True
		logging.warn('emergency_land denied')
		return False

	# users from home or the goal can order the drone to return
	def emergency_return(self, user_facility_id_str):
		logging.info(f'FE_RCV: emergency_return from {user_facility_id_str}')
		if user_facility_id_str in [self.goal_facility.id_str, self.latest_facility.id_str, self.home.id_str]:
			self.queue_message(ToDrone.EMERGENCY_RETURN)
			return True
		logging.warn('emergency_return denied')
		return False

	# if the drone is waiting to take off at facility_id, start the mission to home
	def allow_takeoff(self, user_facility_id_str):
		logging.info(f'FE_RCV: allow_takeoff from {user_facility_id_str}')
		if user_facility_id_str == self.latest_facility.id_str and self.latest_facility.state == facility.State.AWAITING_TAKEOFF:
			self.queue_message(ToDrone.UPDATE, self.generate_update(self.latest_facility, self.goal_facility))
			return True
		logging.warn('allow_takeoff denied')
		return False

	# request the drone to land on user_facility
	def request(self, user_facility_id_str):
		logging.info(f'FE_RCV: request {user_facility_id_str}')
		fac = self.facilities[user_facility_id_str]
		idle = (fac.state == facility.State.IDLE and fac.drone_goal != fac)
		en_route = (fac.state == facility.State.EN_ROUTE and fac.drone_goal != fac)
		returning = (fac.state == facility.State.RETURNING and fac.drone_goal == fac)
		if fac != self.home and (idle or en_route or returning):
			fac.set_drone_requested(True)
			self.check_for_missions()
			return True
		logging.warn('request denied')
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
