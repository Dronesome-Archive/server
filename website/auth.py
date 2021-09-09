from logging import getLogger

import flask
import flask_login
import bson
import markupsafe
from werkzeug.utils import redirect

from app import db, login, oauth
from user import User


# Authentication API; Requests: GET; Response: redirect, flash
auth = flask.Blueprint('auth', __name__, url_prefix='/auth')


# Create user object from db for flask_login
@login.user_loader
def load_user(login_id):
    user = db.users.find_one({'login_id': login_id})
    if not user:
        return None
    else:
        return User(user)


# Redirect user to the OAuth provider
@auth.route('/<string:oauth_server>/login')
def oauth_login(oauth_server):
    if client := oauth.create_client(oauth_server):
        callback_url = flask.url_for('.handle_login', oauth_server=oauth_server, _external=True, _scheme='https')
        return client.authorize_redirect(callback_url)
    getLogger().warning('Invalid oauth server: ' + oauth_server)
    flask.flash('Ungültige Anmeldemethode!', 'error')
    return redirect(flask.url_for('pages.sign_in'))


# With the received OAuth credentials, redirect either to the home page or the account creation page
@auth.route('/<string:oauth_server>/callback')
def handle_login(oauth_server):
    if client := oauth.create_client(markupsafe.escape(oauth_server)):

        # Use authorization code to fetch OIDC info (https://openid.net/specs/openid-connect-core-1_0.html#IDToken)
        id_token = client.authorize_access_token()
        userinfo = client.parse_id_token(id_token)
        if user := db.users.find_one({'oauth_server': oauth_server, 'oauth_token': userinfo.sub}):

            # Account already exists
            login.login_user(User(user))
            return redirect(flask.url_for('pages.account'))
        else:

            # New account
            flask.session['oauth_server'] = markupsafe.escape(oauth_server)
            flask.session['oauth_token'] = userinfo.sub
            return redirect(flask.url_for('pages.register'))
    else:
        flask.flash('Ungültige Anmeldemethode!', 'error')
        return redirect(flask.url_for('pages.sign_in'))


# Invalidate the session and bring back to login page
@auth.route('/logout')
def logout():
    if flask_login.current_user.is_authenticated:
        db.users.update_one({'_id': flask_login.current_user.id}, {'$set': {'login_id': bson.objectid.ObjectId()}})
        flask_login.logout_user()
        flask.flash('Ausgeloggt.')
    return redirect(flask.url_for('pages.sign_in'))
