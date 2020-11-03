import typing
import json
from collections import namedtuple

ERROR_TYPE = namedtuple("ERROR_TYPE", ["null", "invalid", 'convert'])("null", "invalid", 'convert')


class ValidationError(AssertionError):
    """验证数据结构异常
    """

    def __init__(self, msg: typing.Union[str, dict]):
        self.msg = msg

    def out(self):
        if isinstance(self.msg, str):
            return self.msg
        return json.dumps(self.msg, sort_keys=True, indent=4, ensure_ascii=False)

    def __str__(self):
        return self.out()

    def __repr__(self):
        return self.out()


class ModelValidationError(Exception):
    pass
