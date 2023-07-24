from pcs.base.base_enum import BaseEnum, unique


@unique
class UserTypeEnum(BaseEnum):
    master = '主人'
    admin = '管理员'
    guest = '访客'