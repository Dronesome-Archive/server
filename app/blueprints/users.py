import random
import string
import datetime
import logging

import flask
import flask_login
from werkzeug.utils import redirect
from bson.objectid import ObjectId
from flask import current_app

from app.exts import db
from app.user import User


# User management API; Request: POST; Response: redirect, flash
users = flask.Blueprint('users', __name__, url_prefix='/users')


# 'Referer'-header may not be set by the client
def get_referrer():
    return flask.request.referrer if flask.request.referrer else flask.url_for('pages.users')

# Admins can generate one temporary key for their facility so a new user can register
@users.route('/new_key', methods=['POST'])
@flask_login.login_required
def new_key():
    # Get user input
    try:
        can_manage_users = flask.request.form['can_manage_users']
        can_control_drone = flask.request.form['can_control_drone']
    except:
        logging.warning(f'invalid input: {flask.request.form}')
        flask.flash('Fehler. Bitte aktivieren Sie cookies.', 'error')
        return redirect(flask.request.referrer)

    # Check permissions from db
    if flask_login.current_user.get()['can_manage_users']:
        # Generate key with 8 numerals or uppercase ASCII letters (https://stackoverflow.com/q/2257441/10666216)
        key = ''.join([
            random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(current_app.config['NEW_USER_KEY_LENGTH'])
        ])
        new_user = {
            'key': key,
            'expiry': datetime.datetime.now() + datetime.timedelta(minutes=5),
            'can_manage_users': can_manage_users,
            'can_control_drone': can_control_drone
        }
        db.facilities.update_one(
            {'_id': flask_login.current_user.get()['facility_id']},
            {'$set': {'new_user': new_user}}
        )
        logging.info(f"new key: {new_user['key']}")
        flask.flash('Schlüssel: ' + new_user['key'])
    else:
        logging.warning(f'{flask_login.current_user.id_str} cannot manage users')
        flask.flash('Keine Berechtigung.', 'error')

    return redirect(flask.request.referrer)


# Arguments: facility, key, name; Create a new account, if correct creation key is posted
@users.route('/new', methods=['POST'])
def new():

    # Check if user is already logged in
    if flask_login.current_user.is_authenticated:
        flask.flash('Sie sind bereits angemeldet.')
        return redirect(flask.url_for('pages.account'))

    # Get form input
    try:
        name = flask.request.form['name'].strip()[:current_app.config['MAX_NAME_LENGTH']]
        key = flask.request.form['key']
        facility_id = flask.request.form['facility_id']
        oauth_token = flask.session.pop('oauth_token')
        oauth_server = flask.session.pop('oauth_server')
    except:
        logging.warning(f'User creation failed; invalid input {flask.request.form} {flask.session}')
        flask.flash('Fehler. Bitte aktivieren Sie cookies.', 'error')
        return redirect(flask.url_for('pages.sign_in'))

    # Check if user already exists
    if user := db.users.find_one({'oauth.server': oauth_server, 'oauth.token': oauth_token}):
        flask_login.login_user(User(user))
        flask.flash('Der Account existiert bereits.')
        return redirect(flask.url_for('pages.account'))

    # Query key from db
    try:
        facility = db.facilities.find_one({'_id': ObjectId(facility_id)})
        new_user = facility['new_user']
    except Exception as e:
        logging.warning(f'User creation failed, {name}, {oauth_token}, {oauth_server}, {key}, {facility_id}')
        logging.warning(e)
        flask.flash('Fehler.', 'error')
        return redirect(flask.url_for('pages.register'))

    # Check key
    if key == new_user['key']:
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
            logging.warning(f'Key {key} expired')
            flask.flash('Der Schlüssel ist abgelaufen.', 'error')
            return redirect(flask.url_for('pages.register'))
    else:
        logging.warning(f'Invalid key {key}')
        flask.flash('Der Schlüssel ist ungültig.', 'error')
        return redirect(flask.url_for('pages.register'))


# Arguments: name, can_manage_users, can_control_drone, user_id_str; change attributes of a user
@users.route('/edit', methods=['POST'])
@flask_login.login_required
def edit(user_id_str=''):
    if not db.users.find({'_id': ObjectId(user_id_str)}):
        user_id_str = flask_login.current_user.id_str

    # Set values to None if not specified
    name = flask.request.form.get('name', None)
    can_manage_users = flask.request.form.get('can_manage_users', None)
    can_control_drone = flask.request.form.get('can_control_drone', None)

    logging.info(f'Changing user {user_id_str} to {name}, {can_manage_users}, {can_control_drone}')

    if user_id_str == flask_login.current_user.id_str:
        # Change self
        if name:
            db.users.update_one({'_id': user_id_str}, {'$set': {'name': name.strip()[:current_app.config['MAX_NAME_LENGTH']]}})
    elif flask_login.current_user.get()['can_manage_users']:
        # Change other user
        if can_manage_users:
            db.users.update_one({'_id': user_id_str}, {'$set': {'can_manage_users': (can_manage_users == 'True')}})
        if can_control_drone:
            db.users.update_one({'_id': user_id_str}, {'$set': {'can_control_drone': (can_control_drone == 'True')}})
    else:
        logging.warning(f'{flask_login.current_user.id_str} cannot change user {user_id_str}')
        flask.flash('Keine Berechtigung.', 'error')
        return redirect(flask.request.referrer)

    flask.flash('Bearbeitung erfolgreich.')
    return redirect(flask.request.referrer)


# Permanently remove a user's account
@users.route('/delete', methods=['POST'])
@flask_login.login_required
def delete(user_id_str=''):
    if not db.users.find({'_id': ObjectId(user_id_str)}):
        return
    
    if flask_login.current_user.id_str == user_id_str:
        flask_login.logout_user()
        db.users.delete_one({'_id': user_id_str})
        flask.flash('Account gelöscht.')
        return redirect(flask.url_for('pages.sign_in'))
    elif flask_login.current_user.get()['can_manage_users']:
        db.users.delete_one({'_id': user_id_str})
        flask.flash('Account gelöscht.')
    else:
        logging.warning(f'{flask_login.current_user.id_str} cannot delete user {user_id_str}')
        flask.flash('Keine Berechtigung.', 'error')
    logging.info(f'Deleted user {user_id_str}')
    return redirect(flask.request.referrer)
