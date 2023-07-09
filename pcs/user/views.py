from flask import render_template, current_app
from flask import request
from pcs.user import user_bp
from pcs.user.controller.user_controller import UserController

import logging

logger = logging.getLogger(__name__)



@user_bp.route('/login', methods=["POST", "GET"])
def user_login():
    json_data = request.json
    controller = UserController(current_app, request)
    return controller.user_login(json_data)


@user_bp.route('/logout', methods=["POST", "GET"])
def user_logout():
    c = UserController(current_app, request)
    result = c.create_user()
    return render_template('login.html')


@user_bp.route('/register', methods=["POST", "GET"])
def user_register():
    c = UserController(current_app, request)
    result = c.create_user()
    return render_template('login.html')


@user_bp.route('/change_password', methods=["POST", "GET"])
def user_change_password():
    c = UserController(current_app, request)
    result = c.create_user()
    return render_template('login.html')
