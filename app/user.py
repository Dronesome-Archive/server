from app.exts import db


# Class for flask_login.current_user; login_id gets reset everytime the user logs out
class User:
    def __init__(self, db_user):
        self.id = db_user['_id']
        self.login_id = db_user['login_id']
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return str(self.login_id)

    def get(self):
        return db.users.find_one({'_id': self.id})
