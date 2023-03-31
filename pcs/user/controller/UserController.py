from pcs.base.BaseController import BaseController
from pcs.user.model import UserModel
from pcs import db



class UserController(BaseController):
    def create_user(self):
        db.create_all()
        a = 1
