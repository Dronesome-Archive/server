from authlib.integrations.flask_client import OAuth
from authlib.jose import jwt
from werkzeug.utils import redirect
import flask
import pymongo
from os import urandom

app = flask.Flask(__name__)
app.secret_key = urandom(32)
db = pymongo.MongoClient()['app']
app.config.update({
	'GOOGLE_CLIENT_ID': '381175117965-l9op33qit8q13fiat9osch004l10pj82.apps.googleusercontent.com',
	'GOOGLE_CLIENT_SECRET': 'm7CpTfM5trLvd_0Z9saB-kKP',
	'GOOGLE_SERVER_METADATA_URL': 'https://accounts.google.com/.well-known/openid-configuration',
	'GOOGLE_CLIENT_KWARGS': {'scope': 'openid'},
})
oauth = OAuth(app)
oauth.register('google')

@app.route('/test')
def test():
	return "Why are u gay"

@app.route('/login')
def redirect_to_login():
	return oauth.google.authorize_redirect(flask.url_for('confirm_login_data', _external=True))

@app.route('/googlecallback')
def confirm_login_data():
	token = oauth.google.authorize_access_token()
	print('ACCESS TOKEN')
	print(token)
	userinfo = oauth.google.parse_id_token(token)
	print('ID TOKEN')
	print(userinfo)
	print('UID')
	print(userinfo.sub)
	if uid := db.find_
	return redirect(flask.url_for('show_user_data'))

@app.route('/new_user')
def create_new_user():
	pass

@app.route('/main')
def show_user_data():
	pass
