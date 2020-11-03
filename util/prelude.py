from .enum import EnumBase


def is_builtin_type(obj) -> bool:
    """
    检查 obj 是否基础类型
    """
    return isinstance(obj, (int, str, float, bool)) or obj is None
