import flask
import flask_login

from app import db, login


pages = flask.Blueprint('pages', __name__, url_prefix='/')


# Sign in > Log in / Sign up
@pages.route('/sign_in')
@login.unauthorized_handler
def sign_in():
    return flask.render_template('sign_in.html')


# After sign up, register new user
@pages.route('/register')
def register():
    return flask.render_template(
        'register.html',
        facilities=db.facilities.find()
    )


# Log out / change name
@pages.route('/account')
@flask_login.login_required
def account():
    return flask.render_template('account.html', navbar=True, username=flask_login.current_user.get()['name'])


# Drone management
@pages.route('/')
@flask_login.login_required
def courier():
    return flask.render_template('account.html', navbar=True, username=flask_login.current_user.get()['name'])


# Staff management
@pages.route('/staff')
@flask_login.login_required
def staff():
    members = db.users.find({'facility_id': flask_login.current_user.get()['facility_id']})
    return flask.render_template('staff.html', navbar=True, members=members)
