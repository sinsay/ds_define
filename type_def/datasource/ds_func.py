from .ds_field import FieldOrAny


class FuncBase(object):
    pass


class Now(FuncBase):
    """
    用于生成当前时间
    """
    pass


class Count(FuncBase):
    """
    用于生成 Count 语句
    """
    def __init__(self, field: FieldOrAny):
        self._field = field


class Func(object):
    """
    函数操作的基类，用于后续提供统一的分析接口, 当使用了未定义的函数操作时
    自动转为 Sql 的普通字符串处理
    TODO: 处理 getattr 函数及其嵌套的类型
    """
    count = Count
    now = Now


func = Func
