from pcs.common.base.base_enum import BaseEnum, unique


@unique
class LogType(BaseEnum):
    Create = "Create"
    Update = "Update"
    Delete = "Delete"


