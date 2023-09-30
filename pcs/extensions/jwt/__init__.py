import datetime
import jwt
from flask import current_app
# 等待使用


class Auth:
    def __init__(self, user_id, expires):
        self.id = user_id
        self.expires = expires


class Token:
    secret_key = "dlkahdjghj1mhidjkgavd"
    headers = {
        'typ': 'jwt',
        'alg': 'HS256'
    }

    @classmethod
    def gen(cls, user_id, expires: int = 60 * 60):
        conf = current_app.config

        acs_exp = cls.__expired(expires)
        rfh_exp = cls.__expired(expires + 60 * 10)

        acs_payload = cls.__payload(user_id, acs_exp)
        rfh_payload = cls.__payload(user_id, rfh_exp)

        alg: str = cls.headers.get("alg")

        access = jwt.encode(acs_payload, conf.get("SECRET_KEY", cls.secret_key), alg, cls.headers)
        refresh = jwt.encode(rfh_payload, conf.get("SECRET_KEY", cls.secret_key), alg, cls.headers)
        return access, refresh

    @classmethod
    def verify(cls, token: str):
        conf = current_app.config
        alg: str = cls.headers.get("alg")
        payload = jwt.decode(token, conf.get("SECRET_KEY", cls.secret_key), [alg])
        return Auth(**payload), token

    @staticmethod
    def __payload(user_id, exp):
        """
        :param user_id:  用户id
        :param exp: 超时时间
        :return: payload
        """
        return {'id': user_id, 'expires': exp}

    @staticmethod
    def __expired(expires: int):
        return datetime.datetime.now() + datetime.timedelta(seconds=expires)