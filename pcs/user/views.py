from flask import render_template
from pcs.user import user_bp
import logging

logger = logging.getLogger(__name__)


@user_bp.route('/logi')
def login():
    return render_template('login.html')