import typing

base_tags = ["B", "I", "DT", "DTT", "F", "V", "DB", "S"]
numeric_tags = ["I", "F", "DB"]


def _check_tag(t: typing.Any, tag: str) -> bool:
    return getattr(t, "__rpc_tag__", "") == tag


def is_base_type(t: typing.Any) -> bool:
    return getattr(t, "__rpc_tag__", None) in base_tags


def is_list(t: typing.Any) -> bool:
    return _check_tag(t, "L")


def is_dict(t: typing.Any) -> bool:
    return _check_tag(t, "D")


def is_numeric(t: typing.Any) -> bool:
    return getattr(t, "__rpc_tag__", None) in numeric_tags


def is_int(t: typing.Any) -> bool:
    return getattr(t, "__rpc_tag__", None) == "I"


def is_float(t: typing.Any) -> bool:
    return getattr(t, "__rpc_tag__", None) == "F"


def is_string(t: typing.Any) -> bool:
    return _check_tag(t, "S")


def is_boolean(t: typing.Any) -> bool:
    return _check_tag(t, "B")


def is_enum(t: typing.Any) -> bool:
    return _check_tag(t, "E")


def is_model(t) -> bool:
    return getattr(t, "__model_tag__", None) == "MT"
