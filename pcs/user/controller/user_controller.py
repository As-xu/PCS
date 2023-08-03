from pcs.common.base import BaseController
from flask_jwt_extended import create_access_token
from flask import current_app, jsonify
from pcs.common import Sc, Response, errors
from pcs.utils.password import check_password, encrypt_password
import logging

logger = logging.getLogger(__name__)


class UserController(BaseController):
    def create_user(self):
        pass

    def user_login(self, request_data):
        # self.close_autocommit()

        username = request_data.get("user_name")
        password = request_data.get("password")
        user_t = self.get_table_obj('UserTable')

        sc = Sc([("name", "=", username)])
        user_result = user_t.query(sc, fields=["id", "password"])
        if not user_result:
            return Response.error("没有此用户'{0}'".format(username))

        user_info = user_result[0]
        hash_password = user_info.get("password")
        is_valid = check_password(password, hash_password)
        if is_valid:
            return Response.error("用户名或者密码错误")

        access_token = create_access_token(identity=username)
        return Response.json_data({"access_token": access_token})

    def user_register(self, request_data):
        username = request_data.get("user_name")
        password = request_data.get("password")
        email = request_data.get("email")
        user_t = self.get_table_obj('UserTable')

        sc = Sc([("name", "=", username)])
        user_result = user_t.query(sc, fields=["id", "password"])
        if user_result:
            return Response.error("已存在相同用户名'{0}'".format(username))

        hash_password = encrypt_password(password)
        user_t.c

        access_token = create_access_token(identity=username)
        return Response.json_data({"access_token": access_token})