import flask
import flask_login

from app import db, login


pages = flask.Blueprint('pages', __name__, url_prefix='/')


# Sign in > Log in / Sign up
@pages.route('/sign_in')
@login.unauthorized_handler
def sign_in():
    flask.flash('Testmessage')
    flask.flash('Testerror')
    return flask.render_template('sign_in.html')


# After sign up, register new user
@pages.route('/register')
def register():
    return flask.render_template(
        'register.html',
        facilities=[{'id': f['_id'], 'name': f['name']} for f in db.facilities.find()]
    )


# Drone management
@pages.route('/')
@flask_login.login_required
def courier():
    flask.render_template('account.html', navbar=True, username=flask_login.current_user.get()['name'])


# Staff management
@pages.route('/staff')
@flask_login.login_required
def staff():
    pass


# Log out / change name
@pages.route('/account')
@flask_login.login_required
def account():
    pass
