from flask import render_template
from pcs.user import user_bp
import logging

logger = logging.getLogger(__name__)


@user_bp.route('/login')
def index():
    return render_template('index.html')