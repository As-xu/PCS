from pcs.common.base.base_enum import BaseEnum, unique


@unique
class UserTypeEnum(BaseEnum):
    master = 1
    admin = 10
    guest = 100