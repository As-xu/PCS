from pcs.base.base_controller import BaseController
from flask_jwt_extended import create_access_token
from flask import current_app, jsonify
from pcs.common.sql_condition import Sc
import logging

logger = logging.getLogger(__name__)


class UserController(BaseController):
    def create_user(self):
        pass

    def user_login(self, request_data):
        self.close_autocommit()

        username = request_data.get("user_name")
        password = request_data.get("password")
        user_t = self.get_table_obj('UserTable')

        sc = Sc([("user_name", "=", username)])
        user_t.query(sc)

        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)

    def user_register(self, request_data):
        username = request_data.get("username")
        password = request_data.get("password")
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)