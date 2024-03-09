from tts.common.base import Bf

video_bp = Bf.create_bp('video_bp', __name__, url_prefix='/video')

from tts.video import views
