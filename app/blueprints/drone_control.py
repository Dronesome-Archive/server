import flask
import flask_login

from app.drones import drone, facilities

# Drone control API; Requests: POST; Response: redirect, flash
drone_control = flask.Blueprint('drone_control', __name__, url_prefix='/drone_control')


# allow the drone to take off from our facility
@flask_login.login_required
@drone_control.route('/', methods=['POST'])
def control():
    commands = {
        'request': (drone.request, "Kurier angefordert"),
        'allow_takeoff': (drone.allow_takeoff, "Starterlaubnis erteilt"),
        'emergency_return': (drone.emergency_return, "Kurier kehrt um"),
        'emergency_land': (drone.emergency_land, "Notlandung eingeleitet")
    }
    user = flask_login.current_user.get()
    try:
        command, success_message = commands[flask.request.args['command']]
        assert user['can_control_drone']
        if command(user['facility_id']):
            flask.flash(success_message)
    except Exception:
        flask.flash('Fehler', 'error')
    return flask.redirect(flask.request.referrer)
