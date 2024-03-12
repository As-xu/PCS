from tts.common.base.base_enum import BaseEnum, unique


@unique
class DBResultState(BaseEnum):
    """
    执行成功 SUCCESS/ 执行无变动 NOCHANGE/ 执行失败 FAILURE
    """
    SUCCESS = 100
    NOCHANGE = 200
    FAILURE = 300


@unique
class ResponseState(BaseEnum):
    """
    成功 SUCCESS/ 警告 WARNING/ 失败 FAILURE
    """
    SUCCESS = 200
    WARNING = 300
    FAILURE = 400



@unique
class DBType(BaseEnum):
    Postgresql = 'postgresql'
    MySql = 'mysql'
    Redis = 'redis'


@unique
class DBExecMode(BaseEnum):
    """
    执行模式
    成功 QUERY/ 插入 Insert/ 批量插入 Batch Insert / 更新 Update / 批量更新 Batch Update/ 删除 Delete
    """
    QUERY = 'Query'
    INSERT = 'Insert'
    BATCH_INSERT = 'Batch Insert'
    UPDATE = 'Update'
    BATCH_UPDATE = 'Batch Update'
    DELETE = 'Delete'


@unique
class SchedulerStatus(BaseEnum):
    """
    定时任务调度器对象状态
    停止 stopped / 运行 running / 暂停 paused
    """
    stopped = 0
    running = 1
    paused = 2
