from logging import getLogger

import flask
import flask_login
from werkzeug.utils import redirect
from bson.objectid import ObjectId

from app.exts import db, login, oauth
from app.user import User


# Authentication API; Requests: GET; Response: redirect, flash
# TODO: apple auth
auth = flask.Blueprint('auth', __name__, url_prefix='/auth')


# Create user object from db for flask_login
@login.user_loader
def load_user(login_id):
	user = db.users.find_one({'login_id': ObjectId(login_id)})
	if not user:
		return None
	else:
		return User(user)


# Redirect user to the OAuth provider
@auth.route('/<string:oauth_server>/login')
def login(oauth_server):
	if client := oauth.create_client(oauth_server):
		callback_url = flask.url_for('.callback', oauth_server=oauth_server, _external=True, _scheme='https')
		return client.authorize_redirect(callback_url)
	getLogger('app').warning(f'Invalid oauth server: {oauth_server}')
	flask.flash('Ungültige Anmeldemethode!', 'error')
	return redirect(flask.url_for('pages.sign_in'))


# With the received OAuth credentials, redirect either to the home page or the account creation page
@auth.route('/<string:oauth_server>/callback')
def callback(oauth_server):
	if client := oauth.create_client(oauth_server):

		# Use authorization code to fetch OIDC info (https://openid.net/specs/openid-connect-core-1_0.html#IDToken)
		id_token = client.authorize_access_token()
		userinfo = client.parse_id_token(id_token)
		if user := db.users.find_one({'oauth.server': oauth_server, 'oauth.token': userinfo.sub}):

			# Account already exists
			flask_login.login_user(User(user))
			return redirect(flask.url_for('pages.account'))
		else:

			# New account
			flask.session['oauth_server'] = oauth_server
			flask.session['oauth_token'] = userinfo.sub
			return redirect(flask.url_for('pages.register'))
	else:
		getLogger('app').warning(f'Invalid oauth server: {oauth_server}')
		flask.flash('Ungültige Anmeldemethode!', 'error')
		return redirect(flask.url_for('pages.sign_in'))


# Invalidate the session and bring back to login page
@auth.route('/logout')
@flask_login.login_required
def logout():
	db.users.update_one({'_id': ObjectId(flask_login.current_user.id_str)}, {'$set': {'login_id': ObjectId()}})
	oauth_server = flask_login.current_user.get()['oauth']['server']
	flask_login.logout_user()
	flask.flash('Ausgeloggt.')
	if (oauth_server == 'google'):
		# https://stackoverflow.com/q/4202161/
		return redirect('https://accounts.google.com/logout?continue=https://appengine.google.com/_ah/logout?continue=https://droneso.me/')
	else:
		return flask.url_for('pages.sign_in')
