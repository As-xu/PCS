from pcs.common.base import Bf

video_bp = Bf.create_bp('user_bp', __name__, url_prefix='/video')

from pcs.video import views