from tts.common.base import Bf

system_bp = Bf.create_bp('system_bp', __name__, url_prefix='/system')

from tts.system import views
