from os import environ

import flask
import flask_login

from app import drones
from app.exts import db, login


pages = flask.Blueprint('pages', __name__, url_prefix='/')


# Sign in > Log in / Sign up
@pages.route('/sign_in')
@login.unauthorized_handler
def sign_in():
    return flask.render_template('sign_in.html')


# After sign up, register new user
@pages.route('/register')
def register():
    print('register')
    print(drones.facilities)
    for facility in drones.facilities:
        print(facility.id)
        print(facility.name)
    return flask.render_template(
        'register.html',
        facilities=drones.facilities
    )


# Log out / change name
@pages.route('/account')
@flask_login.login_required
def account():
    return flask.render_template(
        'account.html',
        navbar=True,
        username=flask_login.current_user.get()['name']
    )


# Drone management
@pages.route('/')
@flask_login.login_required
def drone():
    user = flask_login.current_user.get()
    user_facility = drones.facilities[str(user['facility_id'])]
    if user_facility == drones.home:
        facilities = drones.facilities
    else:
        facilities = [user_facility, drones.home]
    return flask.render_template(
        'drone.html',
        navbar=True,
        facilities=facilities,
        own=user_facility,
        home=drones.home,
        can_control=user['can_control_drone'],
        mapbox_token=environ['MAPBOX_TOKEN']
    )


# Staff management
@pages.route('/staff')
@flask_login.login_required
def staff():
    # need members as list bc find() only returns a one-time-iterator
    members = [m for m in db.users.find({
        '_id': {'$ne': flask_login.current_user.id},
        'facility_id': flask_login.current_user.get()['facility_id']
    })]
    me = flask_login.current_user.get()
    facility_name = drones.facilities[str(me['facility_id'])].name
    return flask.render_template(
        'staff.html',
        navbar=True,
        members=members,
        me=me,
        facility_name=facility_name
    )
