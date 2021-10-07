import flask
import flask_login

from app.drones import drone, facilities

# Drone control API; Requests: POST; Response: redirect, flash
drone_control = flask.Blueprint('drone_control', __name__, url_prefix='/drone_control')


# request a drone to fly to the our facility
@flask_login.login_required
@drone_control.route('/request', methods=['POST'])
def request():
    user = flask_login.current_user.get()
    if not user['can_control_drone']:
        flask.flash('Keine Berechtigung', 'error')
        return flask.redirect(flask.request.referrer)
    success, msg = [f for f in facilities if f.id == user['facility_id']][0].request_drone()
    flask.flash(msg, 'message' if success else 'error')
    return flask.redirect(flask.request.referrer)


# allow the drone to take off from our facility
@flask_login.login_required
@drone_control.route('/allow_takeoff', methods=['POST'])
def allow_takeoff():
    user = flask_login.current_user.get()
    if not user['can_control_drone']:
        flask.flash('Keine Berechtigung', 'error')
        return flask.redirect(flask.request.referrer)
    drone.allow_takeoff(user['facility_id'])


# if the drone is flying towards you, you can order it to return
@flask_login.login_required
@drone_control.route('/return_to_last_facility', methods=['POST'])
def return_to_last_facility():
    user = flask_login.current_user.get()
    if not user['can_control_drone']:
        flask.flash('Keine Berechtigung', 'error')
        return flask.redirect(flask.request.referrer)
    drone.return_to_last(user['facility_id'])


# if the drone is flying towards you, you can order it to land
@flask_login.login_required
@drone_control.route('/emergency_land', methods=['POST'])
def emergency_land():
    user = flask_login.current_user.get()
    if not user['can_control_drone']:
        flask.flash('Keine Berechtigung', 'error')
        return flask.redirect(flask.request.referrer)
    drone.emergency_land(user['facility_id'])
