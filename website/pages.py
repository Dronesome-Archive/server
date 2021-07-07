from app import app, db
from flask import render_template
import flask_login


################################################################################
# AUTHENTICATION
################################################################################

# Sign in > Log in / Sign up
@app.route('/sign_in')
@flask_login.LoginManager.unauthorized_handler
def page_sign_in():
    return render_template('sign_in.html')


# After sign up, register new user
@app.route('/register')
def page_register():
    return render_template(
        'register.html',
        facilities=[{'id': f._id, 'name': f.name} for f in db.facilities.find()]
    )


################################################################################
# MAIN PAGES
################################################################################

# Drone management
@app.route('/')
@flask_login.login_required
def page_courier():
    pass


# Staff management
@app.route('/staff')
@flask_login.login_required
def page_staff():
    pass


# Log out / change name
@app.route('/account')
@flask_login.login_required
def page_account():
    pass
