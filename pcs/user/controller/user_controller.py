from pcs.base.base_controller import BaseController
from pcs.user.model import user_model
from pcs import db



class UserController(BaseController):
    def create_user(self):
        db.create_all()
        a = 1
