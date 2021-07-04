# Database: app

## users (everyone can view the drone and staff)
- _id
- login_id
- facility_id (user has exactly one facility)
- oauth
	- token
	- server
- name
- can_create_keys (can add new users to the facility)
- can_control_drone (can control the drone)

## facilities
- _id
- name
- new_user
	- key
	- expiry
	- can_create_keys
	- can_control_drone 