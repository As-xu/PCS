from pcs.common.base.base_enum import BaseEnum, unique


@unique
class DBResultState(BaseEnum):
    SUCCESS = 100
    NOCHANGE = 200
    FAILURE = 300


@unique
class ResponseState(BaseEnum):
    SUCCESS = 100
    WARNING = 200
    FAILURE = 300



@unique
class DBType(BaseEnum):
    Postgresql = 'postgresql'
    MySql = 'mysql'
    Redis = 'redis'