from flask import render_template, current_app
from pcs.user import user_bp
from pcs.user.controller.UserController import UserController

import logging

logger = logging.getLogger(__name__)



@user_bp.route('/login', methods=["POST", "GET"])
def login():
    c = UserController()
    result = c.create_user()
    return render_template('login.html')


