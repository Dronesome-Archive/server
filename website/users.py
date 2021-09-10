import random
import string
import datetime
from logging import getLogger

import flask
import flask_login
import bson
import markupsafe
from werkzeug.utils import redirect

from app import db
from user import User


# User management API; Request: POST; Response: redirect, flash
users = flask.Blueprint('users', __name__, url_prefix='/users')


# Admins can generate one temporary key for their facility so a new user can register
@users.route('/new_key', methods=['POST'])
@flask_login.login_required
def new_key():
    getLogger().info('Creating new user key')
    if 'can_manage_users' in flask_login.current_user.get()['rights']:

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

    getLogger().warning('Creating new user key failed: ' + flask_login.current_user.id + ' does not have the rights')
    flask.flash('Keine Berechtigung.', 'error')
    return redirect(flask.url_for('pages.staff'))


# Arguments: facility, key, name; Create a new account, if correct creation key is posted
@users.route('/new', methods=['POST'])
@flask_login.login_required
def new():
    name = markupsafe.escape(flask.request.args.get('name', None))
    oauth_token = flask.session.get('oauth_token', None)
    oauth_server = flask.session.get('oauth_server', None)
    key = flask.request.args.get('key', None)
    facility_id = flask.request.args.get('facility', None)
    new_user = db.facilities.find_one({'_id': flask.request.args['facility']}).get('new_user', None)
    if not oauth_token or not oauth_server or not key or not facility_id or not new_user:
        getLogger().warning('New user creation failed', name, oauth_token, oauth_server, key, facility_id, new_user)
        flask.flash('Fehler. Bitte aktivieren Sie cookies.', 'error')
        return redirect(flask.url_for('pages.register'))

    if key == new_user.key:
        if new_user.expiry > datetime.datetime.now():
            db_insert = db.users.insert_one({
                'facility_id': facility_id,
                'login_id': bson.objectid.ObjectId(),
                'oauth': {
                    'token': oauth_token,
                    'server': oauth_server
                },
                'name': name,
                'can_manage_users': new_user.can_manage_users,
                'can_control_drone': new_user.can_control_drone
            })
            db_user = db.users.find_one({'_id': db_insert.inserted_id})
            flask_login.login_user(User(db_user))
            return redirect(flask.url_for('pages.account'))
        else:
            getLogger().warning('Key expired ', new_user)
            flask.flash('Der Schlüssel ist abgelaufen.', 'error')
            return redirect(flask.url_for('pages.register'))
    else:
        getLogger().warning('Invalid key ', key, new_user)
        flask.flash('Der Schlüssel ist ungültig.', 'error')
        return redirect(flask.url_for('pages.register'))


# Arguments: name, can_manage_users, can_control_drone, user_id; change attributes of a user
@users.route('/edit', methods=['POST'])
@flask_login.login_required
def edit(user_id):
    user_id = user_id if user_id else flask_login.current_user.id

    # Set values to None if not specified
    name = None if flask.request.args.get('name', None) is None else markupsafe.escape(flask.request.args['name'])
    can_manage_users = None if flask.request.args.get('can_manage_users', None) is None else flask.request.args['can_manage_users'] == "True"
    can_control_drone = None if flask.request.args.get('can_control_drone', None) is None else flask.request.args['can_control_drone'] == "True"

    getLogger().info('Changing user ' + user_id + ' to ' + name + ' ' + can_manage_users + ' ' + can_control_drone)

    if user_id == flask_login.current_user.id:
        # Change self
        if name is not None:
            db.users.update_one({'_id': flask_login.current_user.id}, {'$set': {'name': name}})
    elif flask_login.current_user.get()['can_manage_users']:
        # Change other user
        if name is not None:
            db.users.update_one({'_id': flask_login.current_user.id}, {'$set': {'name': name}})
        if can_manage_users is not None:
            db.users.update_one({'_id': flask_login.current_user.id}, {'$set': {'can_manage_users': can_manage_users}})
        if can_control_drone is not None:
            db.users.update_one({'_id': flask_login.current_user.id}, {'$set': {'can_control_drone': can_control_drone}})
    else:
        getLogger().warning(flask_login.current_user.id + " can't change user " + user_id)
        flask.flash('Keine Berechtigung.', 'error')

    flask.flash('Bearbeitung erfolgreich.')
    return redirect(flask.request.referrer)


# Permanently remove a user's account
@users.route('/delete', methods=['POST'])
@flask_login.login_required
def delete(user_id):
    user_id = user_id if user_id else flask_login.current_user.id
    if flask_login.current_user.id == user_id:
        flask_login.logout_user()
        db.users.delete_one({'_id': user_id})
        flask.flash('Account gelöscht.')
        return redirect(flask.url_for('pages.sign_in'))
    elif flask_login.current_user.get()['can_manage_users']:
        db.users.delete_one({'_id': user_id})
        flask.flash('Account gelöscht.')
    else:
        getLogger().warning(flask_login.current_user.id + " can't delete user " + user_id)
        flask.flash('Keine Berechtigung.', 'error')
    getLogger().info('Deleted user ' + user_id)
    return redirect(flask.request.referrer)
