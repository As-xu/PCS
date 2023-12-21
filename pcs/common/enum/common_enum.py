from pcs.common.base.base_enum import BaseEnum, unique


@unique
class LogType(BaseEnum):
    Create = "Create"
    Update = "Update"
    Delete = "Delete"


@unique
class ProcessStatus(BaseEnum):
    """
    通用流程状态
    等待开始 WaitStart
    处理中 Processing
    暂停 Pause
    结束 Finish
    错误 Error
    跳过 Skip
    """
    WaitStart = 10
    Processing = 20
    Pause = 30
    Finish = 40
    Error = 50
    Skip = 60


@unique
class CommonObjectStatus(BaseEnum):
    """
    通用对象状态
    草稿 Draft
    可用 Available
    弃用 Deprecated
    取消 Cancel
    完成 Completed
    异常 Exceptional
    """
    Draft = 10
    Available = 20
    Deprecated = 30
    Cancel = 40
    Completed = 50
    Exceptional = 60
