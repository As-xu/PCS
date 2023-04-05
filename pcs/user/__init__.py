from pcs.base import Bf

user_bp = Bf.create_bp('user_bp', __name__, url_prefix='/user')

from pcs.user import views
from pcs.user.model.user_log_model import UserLogModel
from pcs.user.model.user_model import UserModel
from pcs.user.model.user_login_model import UserLoginModel
