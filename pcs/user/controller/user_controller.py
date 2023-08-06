from pcs.common.base import BaseController
from flask_jwt_extended import create_access_token
from pcs.common.sql_condition import Sc
from pcs.common.response import Response
from pcs.common.enum.user_enum import UserTypeEnum
from pcs.utils.password import check_password, encrypt_password
import logging

logger = logging.getLogger(__name__)


class UserController(BaseController):
    def create_user(self):
        pass

    def user_login(self, request_data):
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
        self.close_autocommit()

        username = request_data.get("user_name")
        password = request_data.get("password")
        phone = request_data.get("phone") or ""
        email = request_data.get("email") or ""
        user_t = self.get_table_obj('UserTable')

        sc = Sc([("name", "=", username)])
        user_result = user_t.query(sc, fields=["id", "password"])
        if user_result:
            return Response.error("已存在相同用户名'{0}'".format(username))

        hash_password = encrypt_password(password)

        user_data = {
            "name": username,
            "password": hash_password,
            "active": True,
            "phone": phone,
            "email": email,
            "show_name": username,
            "user_type": UserTypeEnum.guest.value,
        }
        user_result = user_t.create(user_data)
        if not user_t.exec_success:
            return Response.error("创建用户失败[%s]" % user_t.error_msg)

        access_token = create_access_token(identity=username)
        self.commit()
        return Response.json_data({"access_token": access_token})


