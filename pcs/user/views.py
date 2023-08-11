from flask import render_template
from flask import request
from pcs.user import user_bp
from pcs.user.controller.user_controller import UserController
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, get_jwt_header

import logging

logger = logging.getLogger(__name__)


@user_bp.route('/login', methods=["POST", "GET"])
def user_login():
    json_data = request.json
    if request.method == 'GET':
        return render_template('login.html')
    else:
        controller = UserController(request)
        return controller.user_login(json_data)


@user_bp.route('/logout', methods=["POST", "GET"])
@jwt_required(optional=True)
def user_logout():
    get_jwt()
    c = UserController(request)
    return c.user_logout()


@user_bp.route('/register', methods=["POST", "GET"])
def user_register():
    json_data = request.json
    if request.method == 'GET':
        return render_template('login.html')
    else:
        controller = UserController(request)
        return controller.user_register(json_data)


@user_bp.route('/change_password', methods=["POST", "GET"])
def user_change_password():
    c = UserController(request)
    return render_template('login.html')
