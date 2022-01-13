import flask
import flask_login

from app.drones import drone, facilities

# Drone control API; Requests: GET; Response: redirect, flash
drone_control = flask.Blueprint('drone_control', __name__, url_prefix='/drone_control')


# allow the drone to take off from our facility
@flask_login.login_required
@drone_control.route('/<string:command>', methods=['GET'])
def control(command):
    commands = {
        'request': (drone.request, "Kurier angefordert"),
        'allow_takeoff': (drone.allow_takeoff, "Starterlaubnis erteilt"),
        'emergency_return': (drone.emergency_return, "Kurier kehrt um"),
        'emergency_land': (drone.emergency_land, "Notlandung eingeleitet")
    }
    user = flask_login.current_user.get()
    try:
        func, success_message = commands[command]
        assert user['can_control_drone']
        if func(user['facility_id']):
            flask.flash(success_message)
    except Exception:
        flask.flash('Fehler', 'error')
    return flask.redirect(flask.request.referrer)
