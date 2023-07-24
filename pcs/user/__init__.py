from pcs.base import Bf

user_bp = Bf.create_bp('user_bp', __name__, url_prefix='/user')

from pcs.user import views
