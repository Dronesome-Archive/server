import imp
from app.exts import db
from bson.objectid import ObjectId


# Class for flask_login.current_user; login_id gets reset everytime the user logs out
class User:
    def __init__(self, db_user):
        self.id_str = str(db_user['_id'])
        self.login_id_str = str(db_user['login_id'])
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return self.login_id_str

    def get(self):
        return db.users.find_one({'_id': ObjectId(self.id_str)})
