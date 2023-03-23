from pcs.base import Bf

user_bp = Bf.create_bp('user_bp', __name__, url_prefix='/user')

from pcs.user import views
from pcs.user.model.UserLogModel import UserLogModel
from pcs.user.model.UserModel import UserModel
from pcs.user.model.UserLoginModel import UserLoginModel
