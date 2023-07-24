from pcs.base.base_controller import BaseController
from flask_jwt_extended import create_access_token
from flask import current_app, jsonify
import logging

logger = logging.getLogger(__name__)


class UserController(BaseController):
    def create_user(self):
        pass

    def user_login(self, request_data):
        username = request_data.get("user_name")
        password = request_data.get("password")
        user_table = current_app.gto("user")
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)

    def user_register(self, request_data):
        username = request_data.get("username")
        password = request_data.get("password")
        db = current_app.db

        # Notice that we are passing in the actual sqlalchemy user object here
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)