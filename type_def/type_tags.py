import typing
from flask_restplus import fields

rpc_serializer = '__serializer__'

rpc_doc_args_key = "_rpc_doc_args"
rpc_doc_type_key = "_rpc_doc_type"
rpc_doc_resp_key = "_rpc_doc_resp"


MYSQL = 'MYSQL'
SUPPORT_INDEX_TYPES = {
    MYSQL: ['hash', 'btree']
}

_basic_fields = [
    "required", "default_value", "default", "description",
    "max_items", "min_items", "maximum", "minimum",
    "min", "max"
]

_flask_field_mapping: typing.Dict[typing.Any, typing.Any] = {
    fields.Boolean: bool,
    fields.Integer: int,
    fields.Float: float,
    fields.String: str,
}


def convert_flask_type_to_dict(field: fields.Raw, place: str) -> typing.Dict[str, typing.Dict]:
    d = {}
    for key in _basic_fields:
        value = getattr(field, key, None)
        if value is None:
            continue
        d[key] = value

    t = _flask_field_mapping.get(type(field), None)
    if t is None:
        raise TypeError(f"flask restplus doc 的 params 定义不支持类型: {field}")

    d["type"] = t
    d["in"] = place
    return d


def allow_addition():
    def w(cls):
        # doc 只加在原始的函数上
        while hasattr(cls, "__wrapped__"):
            cls = cls.__wrapped__
        setattr(cls, "allow_addition", True)
        return cls

    return w
