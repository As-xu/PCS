import logging
from flask import render_template
from flask import request
from pcs.user import user_bp as bp
from pcs.user.controller.user import UserController

logger = logging.getLogger(__name__)


@bp.route('/login', methods=["POST", "GET"], no_verify=True)
def user_login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        json_data = request.json
        controller = UserController(request)
        return controller.user_login(json_data)


@bp.route('/logout', methods=["POST"], no_verify=True)
def user_logout():
    c = UserController(request)
    return c.user_logout()


@bp.route('/register', methods=["POST", "GET"], no_verify=True)
def user_register():
    json_data = request.json
    if request.method == 'GET':
        return render_template('login.html')
    else:
        controller = UserController(request)
        return controller.user_register(json_data)


@bp.route('/change_password', methods=["POST", "GET"])
def user_change_password():
    c = UserController(request)
    return render_template('login.html')
