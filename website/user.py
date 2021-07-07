from app import db


# Class for flask_login.current_user; login_id gets reset everytime the user logs out
class User:
    def __init__(self, db_user):
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
        self.id = db_user['id']
        self.login_id = db_user['login_id']

    def get_id(self):
        return str(self.login_id)

    def get(self):
        return db.users.find_one({'_id': self.id})