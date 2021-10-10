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
        'request': drone.request,
        'allow_takeoff': drone.allow_takeoff,
        'return': drone.return_to_last,
        'land': drone.emergency_land
    }
    user = flask_login.current_user.get()
    try:
        command = commands[flask.request.args['command']]
    except IndexError:
        flask.flash('Fehler', 'error')
    else:
        if user['can_control_drone']:
            if command(user['facility_id']):
                flask.flash('Starterlaubnis erteilt')
            else:
                flask.flash('Fehler', 'error')
        else:
            flask.flash('Keine Berechtigung', 'error')
    return flask.redirect(flask.request.referrer)
