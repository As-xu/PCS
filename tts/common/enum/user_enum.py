from tts.common.base.base_enum import BaseEnum, unique


@unique
class UserType(BaseEnum):
    master = 1
    admin = 10
    guest = 100


@unique
class LoginType(BaseEnum):
    Login = "Login"
    Logout = "Logout"