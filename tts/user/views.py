import logging
from flask import render_template
from flask import request
from tts.user import user_bp as bp
from tts.user.controller.user import UserController

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


@bp.route('/registerUser', methods=["POST", "GET"], no_verify=True)
def user_register():
    json_data = request.json
    if request.method == 'GET':
        return render_template('login.html')
    else:
        controller = UserController(request)
        return controller.user_register(json_data)


@bp.route('/changePasswd', methods=["POST", "GET"])
def user_change_password():
    json_data = request.json
    c = UserController(request)
    return c.change_password(json_data)


@bp.route('/getUserInfo', methods=["POST", "GET"])
def query_user_info():
    json_data = request.json
    c = UserController(request)
    return c.query_user_info(json_data)


@bp.route('/getRouters', methods=["POST", "GET"])
def query_user_routers():
    json_data = request.json
    return UserController(request).query_user_routers(json_data)