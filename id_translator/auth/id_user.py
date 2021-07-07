"""
Implementation of User class for Flask-login
"""

from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, _id):
        self.id = _id
        super().__init__()
