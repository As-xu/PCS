import json as _json
import decimal
import typing as t
import uuid
from datetime import date, datetime
from .common_const import DATETIME_FORMAT, DATE_FORMAT
import dataclasses

class JSONEncoder(_json.JSONEncoder):
    """
        PCS JSONEncoder
    """

    def default(self, o: t.Any) -> t.Any:
        if isinstance(o, datetime):
            return o.strftime(DATETIME_FORMAT)
        elif isinstance(o, date):
            return o.strftime(DATE_FORMAT)
        if isinstance(o, (decimal.Decimal, uuid.UUID)):
            return str(o)
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if hasattr(o, "__html__"):
            return str(o.__html__())
        return super().default(o)


class JSONDecoder(_json.JSONDecoder):
    """
        PCS JSONDecoder
    """