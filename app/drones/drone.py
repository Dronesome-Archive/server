from enum import Enum
from logging import getLogger

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
				'id': goal.id_str,
				'pos': goal.pos
			}
		}

	# put a message into self.outbox
	def queue_message(self, msg_type, content={}):
		getLogger('app').info(f"DR_QUE: {msg_type}: {content}")
		self.outbox = content
		self.outbox['type'] = msg_type.value

	# if we're waiting at home, we can do a new mission
	def check_for_missions(self):
		pending = [fac for fac_id, fac in self.facilities.items() if fac.drone_requested]
		getLogger('app').info(f'Found pending missions: {pending}')
		if len(pending) and self.goal_facility == self.latest_facility == self.home:
			pending.sort(key=lambda f: f.drone_requested_on)
			getLogger('app').info(f"starting mission to '{pending[0].name}'")
			self.goal_facility = pending[0]
			self.latest_facility.set_state(facility.State.AWAITING_TAKEOFF, self.goal_facility)


	####################################################################################################################
	# ORDERS FROM COMPANION
	####################################################################################################################

	# we received a heartbeat from the drone
	def on_heartbeat(self, pos, battery):
		self.pos = pos
		self.battery = battery
		if (self.goal_facility == self.home or self.goal_facility.state != facility.State.IDLE):
			self.goal_facility.send(ToFrontend.HEARTBEAT, pos=pos, battery=battery)
		self.latest_facility.send(ToFrontend.HEARTBEAT, pos=pos, battery=battery)

	# we got a state update from the drone; even if drone was returning, goal_facility_id is still the original goal's id
	def on_state_update(self, state, current_facility_id_str, goal_facility_id_str):
		current_facility = self.facilities[current_facility_id_str]
		goal_facility = self.facilities[goal_facility_id_str]
		getLogger('app').info(f"{state.value} from {current_facility.name} to {goal_facility.name}")
		if goal_facility != self.goal_facility and state != State.UPDATING:
			getLogger('app').warning(f"drone's goal facility '{goal_facility.name}' not equal to ours: '{self.goal_facility.name}'")
			self.goal_facility = goal_facility

		if state in [State.IDLE]:
			self.goal_facility = self.home
			if current_facility == self.home:
				# landed on home, errand complete
				self.latest_facility.set_state(facility.State.IDLE, self.goal_facility)
				self.goal_facility.set_state(facility.State.IDLE, self.goal_facility)
				self.check_for_missions()
			else:
				# landed on non-home
				current_facility.set_state(facility.State.AWAITING_TAKEOFF, self.goal_facility)
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
		self.goal_facility.send(ToFrontend.DRONE_STATE, state=state)
		self.latest_facility.send(ToFrontend.DRONE_STATE, state=state)


	####################################################################################################################
	# ORDERS FROM FRONTEND
	####################################################################################################################

	# users from home or the goal can order the drone to emergency land
	def emergency_land(self, user_facility_id_str):
		getLogger('app').info(f'FE_RCV: emergency_land from {self.facilities[user_facility_id_str].name}')
		if user_facility_id_str in [self.goal_facility.id_str, self.latest_facility.id_str, self.home.id_str]:
			self.queue_message(ToDrone.EMERGENCY_LAND)
			return True
		getLogger('app').warning('emergency_land denied')
		return False

	# users from home or the goal can order the drone to return
	def emergency_return(self, user_facility_id_str):
		getLogger('app').info(f'FE_RCV: emergency_return from {self.facilities[user_facility_id_str].name}')
		if user_facility_id_str in [self.goal_facility.id_str, self.latest_facility.id_str, self.home.id_str]:
			self.queue_message(ToDrone.EMERGENCY_RETURN)
			return True
		getLogger('app').warning('emergency_return denied')
		return False

	# if the drone is waiting to take off at facility_id, start the mission to home
	def allow_takeoff(self, user_facility_id_str):
		getLogger('app').info(f'FE_RCV: allow_takeoff from {self.facilities[user_facility_id_str].name}')
		if user_facility_id_str == self.latest_facility.id_str and self.latest_facility.state == facility.State.AWAITING_TAKEOFF:
			self.queue_message(ToDrone.UPDATE, self.generate_update(self.latest_facility, self.goal_facility))
			return True
		getLogger('app').warning('allow_takeoff denied')
		return False

	# request the drone to land on user_facility
	def request(self, user_facility_id_str):
		getLogger('app').info(f'FE_RCV: request from {self.facilities[user_facility_id_str].name}')
		fac = self.facilities[user_facility_id_str]
		if fac != self.home and fac != self.goal_facility and fac.state != facility.State.AWAITING_TAKEOFF:
			fac.set_drone_requested(True)
			self.check_for_missions()
			return True
		getLogger('app').warning('request denied')
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
