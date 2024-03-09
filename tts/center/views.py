from flask import render_template
from tts.center import center_bp
import logging

logger = logging.getLogger(__name__)


@center_bp.route('/')
def index():
    return render_template('index.html')

