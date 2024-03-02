import logging
from pcs.utils.password import check_password, encrypt_password
from flask_jwt_extended import create_access_token, set_access_cookies, unset_access_cookies
from pcs.common.base import BaseController
from pcs.common.sql_condition import Sc
from pcs.common.response import Response
from pcs.common.enum.user_enum import UserType
from pcs.common.enum.common_enum import LogType


logger = logging.getLogger(__name__)


class UserController(BaseController):
    def user_login(self, request_data):
        username = request_data.get("user_name")
        password = request_data.get("password")
        user_t = self.get_table('UserTable')
        user_login_t = self.get_table('UserLoginTable')

        sc = Sc([("=", "name", username)])
        user_result = user_t.query(sc, fields=["id", "password"])
        if not user_result:
            return Response.error("没有此用户'{0}'".format(username))

        user_info = user_result[0]
        hash_password = user_info.get("password")
        user_id = user_info.get("id")
        is_valid = check_password(password, hash_password)
        if not is_valid:
            return Response.error("用户名或者密码错误")

        user_login_t.user_login(user_id)

        access_token = create_access_token(identity={"user_id": user_id, "user_name": username})
        response = Response.success("登录成功!")
        set_access_cookies(response, access_token)
        logger.warning(response.headers)
        return response

    def user_register(self, request_data):
        self.close_autocommit()
        user_t = self.get_table(self.tables.UserTable)
        user_log_t = self.get_table(self.tables.UserLogTable)

        username = request_data.get("user_name")
        password = request_data.get("password")
        phone = request_data.get("phone") or ""
        email = request_data.get("email") or ""

        sc = Sc([("=", "name", username)])
        user_result = user_t.query(sc, fields=["id", "password"])
        if user_result:
            return Response.error("已存在相同用户名")

        hash_password = encrypt_password(password)

        user_data = {
            "name": username, "password": hash_password, "active": True,
            "phone": phone, "email": email, "show_name": username, "user_type": UserType.guest.value,
        }
        user_result = user_t.create(user_data)

        user_id = user_result.get("id")
        user_log_t.add_log(user_id, LogType.Create.value, "创建用户[{0}]成功".format(username))
        self.commit()
        return Response.success()

    def user_logout(self):
        if not self.user_id:
            response = Response.success("尚未登录")
            unset_access_cookies(response)
            return response
        user_login_t = self.get_table(self.tables.UserLoginTable)
        user_login_t.user_logout()
        response = Response.success()
        unset_access_cookies(response)
        return response

    def query_user_info(self, json_data):
        """
        获取用户信息
        :param json_data:
        :return:
        """
        # 假数据
        fake_data = {
            "permissions": [
                "*:*:*"
            ],
            "roles": [
                "admin"
            ],
            "user": {
                "createBy": "admin",
                "createTime": "2023-04-23 16:11:38",
                "updateBy": None,
                "updateTime": None,
                "remark": "管理员",
                "userId": 1,
                "deptId": 103,
                "userName": "admin",
                "nickName": "若依",
                "email": "ry@163.com",
                "phonenumber": "15888888888",
                "sex": "1",
                "avatar": "",
                "password": "$2a$10$7JB720yubVSZvUI0rEqK/.VqGOZTH.ulu33dHOiBE8ByOhJIrdAu2",
                "status": "0",
                "delFlag": "0",
                "loginIp": "112.41.1.104",
                "loginDate": "2024-02-29T23:47:29.000+08:00",
                "dept": {"createBy": None,
                    "createTime": None,
                    "updateBy": None,
                    "updateTime": None,
                    "remark": None,
                    "deptId": 103,
                    "parentId": 101,
                    "ancestors": "0,100,101",
                    "deptName": "研发部门",
                    "orderNum": 1,
                    "leader": "若依",
                    "phone": None,
                    "email": None,
                    "status": "0",
                    "delFlag": None,
                    "parentName": None,
                    "children": []
                },
                "roles": [
                    {
                        "createBy": None,
                        "createTime": None,
                        "updateBy": None,
                        "updateTime": None,
                        "remark": None,
                        "roleId": 1,
                        "roleName": "超级管理员",
                        "roleKey": "admin",
                        "roleSort": 1,
                        "dataScope": "1",
                        "menuCheckStrictly": False,
                        "deptCheckStrictly": False,
                        "status": "0",
                        "delFlag": None,
                        "flag": False,
                        "menuIds": None,
                        "deptIds": None,
                        "permissions": None,
                        "admin": True
                    }
            ],
            }
        }

        return Response.json_data(fake_data)

    def query_user_routers(self, json_data):
        """
        获取菜单信息
        :param json_data:
        :return:
        """
        user_id = json_data.get("user_id")
        menu_t = self.get_table(self.tables.SystemMenuTable)
        sc = Sc([])
        menu_result = menu_t.query(sc)
        return Response.json_data(menu_result)


    def change_password(self, json_data):
        return Response.success()