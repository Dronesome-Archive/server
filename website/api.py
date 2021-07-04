import random
import string
import datetime

import flask
import flask_login
import bson
from app import db, login, oauth
import markupsafe
from werkzeug.utils import redirect

from user import User

bp = flask.Blueprint('api', __name__, url_prefix='/api')


# Create user object from db for flask_login
@login.user_loader
def load_user(login_id):
    user = db.users.find_one({'login_id': login_id})
    if not user:
        return None
    else:
        return User(user)


# Redirect user to the OAuth provider
@bp.route('/<string:oauth_server>/login')
def oauth_login(oauth_server):
    if client := oauth.create_client(markupsafe.escape(oauth_server)):
        callback_url = flask.url_for('handle_login', oauth_server=oauth_server, _external=True)
        return client.authorize_redirect(callback_url)
    return 400


# With the received OAuth credentials, redirect either to the home page or the account creation page
@bp.route('/<string:oauth_server>/callback')
def handle_login(oauth_server):
    if client := oauth.create_client(markupsafe.escape(oauth_server)):

        # Use authorization code to fetch OIDC info (https://openid.net/specs/openid-connect-core-1_0.html#IDToken)
        id_token = client.authorize_access_token()
        userinfo = client.parse_id_token(id_token)
        if user := db.users.find_one({'oauth_server': oauth_server, 'oauth_token': userinfo.sub}):

            # Account already exists
            login.login_user(User(user))
            return redirect(flask.url_for('courier'))
        else:

            # New account
            flask.session['oauth_server'] = markupsafe.escape(oauth_server)
            flask.session['oauth_token'] = userinfo.sub
            return redirect(flask.url_for('new_user'))


# Invalidate the session and bring back to login page
@bp.route('/logout')
def logout():
    if flask_login.current_user.is_authenticated:
        db.users.update_one({'_id': flask_login.current_user.id}, {'$set': {'login_id': bson.objectid.ObjectId()}})
        flask_login.logout_user()
    return redirect(flask.url_for('login'))


# Admins can generate one temporary key for their facility so a new user can register
@flask_login.login_required
@bp.route('/new_user_key')
def new_user_key():
    if 'create_keys' in flask_login.current_user.get()['rights']:

        # Generate key with 8 numerals or uppercase ASCII letters (https://stackoverflow.com/q/2257441/10666216)
        new_user = {
            'key': ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8)),
            'expiry': datetime.datetime.now() + datetime.timedelta(minutes=5)
        }
        db.facilities.update_one(
            {'_id': flask_login.current_user.get()['facility']},
            {'$set': {'new_user': new_user}}
        )
        flask.flash('Schlüssel: ' + new_user['key'])

    return redirect(flask.url_for('staff'))


# Arguments: facility, key, name; Create a new account, if correct creation key is posted
@bp.route('/register', methods=['POST'])
def create_new_user():
    name = markupsafe.escape(flask.request.args.get('name', None))
    oauth_token = flask.session.get('oauth_token', None)
    oauth_server = flask.session.get('oauth_server', None)
    key = flask.request.args.get('key', None)
    facility_id = flask.request.args.get('facility', None)
    new_user = db.facilities.find_one({'_id': flask.request.args['facility']}).get('new_user', None)
    if not oauth_token or not oauth_server or not key or not facility_id or not new_user:
        return 400

    if key == new_user.key:
        if new_user.expiry > datetime.datetime.now():
            db.users.insert_one({
                'facility_id': facility_id,
                'login_id': bson.objectid.ObjectId(),
                'oauth': {
                    'token': oauth_token,
                    'server': oauth_server
                },
                'name': name,
                'can_create_keys': new_user.can_create_keys,
                'can_control_drone': new_user.can_control_drone
            })
        else:
            return 'Der Schlüssel ist abgelaufen.', 400
    else:
        return 'Der Schlüssel ist ungültig', 400
