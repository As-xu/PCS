from pcs.common.base import Bf

video_bp = Bf.create_bp('video_bp', __name__, url_prefix='/video')

from pcs.video import views