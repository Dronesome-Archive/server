from app import app, db
from flask import render_template

################################################################################
# AUTHENTICATION
################################################################################

# Sign in > Log in / Sign up
@app.route('/sign_in')
def page_sign_in():
    pass


# After sign up, register new user
@app.route('/register')
def page_register():
    return render_template(
        'register.html',
        facilities=[{'id': f._id, 'name': f.name} for f in db.facilities.find_all()]
    )


################################################################################
# MAIN PAGES
################################################################################

# Drone management
@app.route('/courier')
def page_courier():
    pass


# Staff management
@app.route('/staff')
def page_staff():
    pass


# Log out / change name
@app.route('/account')
def page_account():
    pass
