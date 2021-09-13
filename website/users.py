import random
import string
import datetime

import flask
import flask_login
import markupsafe
from werkzeug.utils import redirect
from bson.objectid import ObjectId

from app import db
from user import User
import log


# User management API; Request: POST; Response: redirect, flash
users = flask.Blueprint('users', __name__, url_prefix='/users')


# Admins can generate one temporary key for their facility so a new user can register
@users.route('/new_key', methods=['POST'])
@flask_login.login_required
def new_key():
    log.info('Creating new user key')
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

    log.warn('Creating new user key failed:', flask_login.current_user.id, 'does not have the rights')
    flask.flash('Keine Berechtigung.', 'error')
    return redirect(flask.url_for('pages.staff'))


# Arguments: facility, key, name; Create a new account, if correct creation key is posted
@users.route('/new', methods=['POST'])
def new():

    # Get form input
    name = markupsafe.escape(flask.request.form.get('name', None))
    oauth_token = flask.session.get('oauth_token', None)
    oauth_server = flask.session.get('oauth_server', None)
    key = flask.request.form.get('key', None)
    facility_id = flask.request.form.get('facility_id', None)
    if not oauth_token or not oauth_server or not key or not facility_id:
        log.warn('User creation failed; invalid input', name, oauth_token, oauth_server, key, facility_id)
        flask.flash('Fehler. Bitte aktivieren Sie cookies.', 'error')
        return redirect(flask.url_for('pages.sign_in'))

    # Query key from db
    new_user = {}
    try:
        facility = db.facilities.find_one({'_id': ObjectId(facility_id)})
        new_user = facility['new_user']
    except Exception as e:
        log.warn('User creation failed', name, oauth_token, oauth_server, key, facility_id)
        log.warn(e)
        flask.flash('Fehler.', 'error')
        return redirect(flask.url_for('pages.register'))

    # Check key
    if str(key) == str(new_user['key']):
        if new_user['expiry'] > datetime.datetime.now():
            db_insert = db.users.insert_one({
                'facility_id': ObjectId(facility_id),
                'login_id': ObjectId(),
                'oauth': {
                    'token': oauth_token,
                    'server': oauth_server
                },
                'name': name,
                'can_manage_users': new_user['can_manage_users'],
                'can_control_drone': new_user['can_control_drone']
            })
            db.facilities.update_one({'_id': ObjectId(facility_id)}, {'$currentDate': {'new_user.expiry': True}})
            db_user = db.users.find_one({'_id': db_insert.inserted_id})
            flask_login.login_user(User(db_user))
            return redirect(flask.url_for('pages.account'))
        else:
            log.warn('Key expired', key, new_user)
            flask.flash('Der Schlüssel ist abgelaufen.', 'error')
            return redirect(flask.url_for('pages.register'))
    else:
        log.warn('Invalid key', key, new_user)
        flask.flash('Der Schlüssel ist ungültig.', 'error')
        return redirect(flask.url_for('pages.register'))


# Arguments: name, can_manage_users, can_control_drone, user_id; change attributes of a user
@users.route('/edit', methods=['POST'])
@flask_login.login_required
def edit(user_id=None):
    try:
        user_id = ObjectId(user_id)
    except:
        user_id = flask_login.current_user.id

    # Set values to None if not specified
    name = None if flask.request.form.get('name', None) is None else markupsafe.escape(flask.request.form['name'])
    can_manage_users = None if flask.request.form.get('can_manage_users', None) is None else flask.request.form['can_manage_users'] == "True"
    can_control_drone = None if flask.request.form.get('can_control_drone', None) is None else flask.request.form['can_control_drone'] == "True"

    log.info('Changing user', user_id, 'to', name, can_manage_users, can_control_drone)

    if user_id == flask_login.current_user.id:
        # Change self
        if name is not None:
            db.users.update_one({'_id': user_id}, {'$set': {'name': name}})
        if can_control_drone is not None:
            db.users.update_one({'_id': user_id}, {'$set': {'can_control_drone': can_control_drone}})
    elif flask_login.current_user.get()['can_manage_users']:
        # Change other user
        if name is not None:
            db.users.update_one({'_id': user_id}, {'$set': {'name': name}})
        if can_manage_users is not None:
            db.users.update_one({'_id': user_id}, {'$set': {'can_manage_users': can_manage_users}})
        if can_control_drone is not None:
            db.users.update_one({'_id': user_id}, {'$set': {'can_control_drone': can_control_drone}})
    else:
        log.warn(flask_login.current_user.id, "can't change user", user_id)
        flask.flash('Keine Berechtigung.', 'error')

    flask.flash('Bearbeitung erfolgreich.')
    return redirect(flask.request.referrer)


# Permanently remove a user's account
@users.route('/delete', methods=['POST'])
@flask_login.login_required
def delete(user_id=None):
    try:
        user_id = ObjectId(user_id)
    except:
        user_id = flask_login.current_user.id
    if flask_login.current_user.id == user_id:
        flask_login.logout_user()
        db.users.delete_one({'_id': user_id})
        flask.flash('Account gelöscht.')
        return redirect(flask.url_for('pages.sign_in'))
    elif flask_login.current_user.get()['can_manage_users']:
        db.users.delete_one({'_id': user_id})
        flask.flash('Account gelöscht.')
    else:
        log.warn(flask_login.current_user.id, " can't delete user ", user_id)
        flask.flash('Keine Berechtigung.', 'error')
    log.info('Deleted user ' + user_id)
    return redirect(flask.request.referrer)
