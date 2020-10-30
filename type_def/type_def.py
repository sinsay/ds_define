import copy
import datetime
import json
import typing

import pytz

from .type_base import ValidationError, Validate, RpcType, ERROR_TYPE


class Void(RpcType):
    __rpc_tag__ = "V"

    def __init__(self):
        RpcType.__init__(self, None, False)

    def get_type(self):
        return "void"

    def get_column_type(self):
        pass

    def serialize(self, value: any) -> str:
        return 'null'

    def deserialize(self, value: any) -> None:
        return None


class Bool(RpcType):
    __rpc_tag__ = "B"
    default_error_messages = {
        ERROR_TYPE.invalid: 'Must be a valid boolean but get type: {input_type}'
    }
    TRUE_VALUES = {
        't', 'T',
        'y', 'Y', 'yes', 'YES',
        'true', 'True', 'TRUE',
        'on', 'On', 'ON',
        '1', 1,
        True
    }
    FALSE_VALUES = {
        'f', 'F',
        'n', 'N', 'no', 'NO',
        'false', 'False', 'FALSE',
        'off', 'Off', 'OFF',
        '0', 0, 0.0,
        False
    }

    NULL_VALUES = {'null', 'Null', 'NULL', '', None}

    def get_type(self):
        return "bool"

    def get_column_type(self):
        return "Boolean"

    def serialize(self, value: any) -> typing.Union[bool, None]:
        if value in self.TRUE_VALUES:
            return True
        elif value in self.FALSE_VALUES:
            return False
        if value in self.NULL_VALUES and not self.required:
            return None
        return bool(value)

    def deserialize(self, value: any) -> bool:
        if value in self.TRUE_VALUES:
            return True
        elif value in self.FALSE_VALUES:
            return False
        elif value in self.NULL_VALUES and not self.required:
            return value
        self.fail(ERROR_TYPE.invalid, input_type=type(value))


class Integer(RpcType):
    __rpc_tag__ = "I"
    default_error_messages = {
        ERROR_TYPE.invalid: 'A valid integer is required but get type: {input_type}',
    }

    def get_type(self):
        """
        这里负责将 python 的类型信息转换为 gRPC 类型, 不过在这里转换合适吗？
        :return:
        """
        return "int"

    def get_column_type(self):
        return "Integer"

    def serialize(self, value: any) -> int:
        if not value:
            return value
        return int(value)

    def deserialize(self, value: any) -> any:
        if value is None:
            return value

        try:
            return int(value)
        except (ValueError, TypeError):
            self.fail(ERROR_TYPE.convert, input_type=type(value))


class Time(RpcType):
    __rpc_tag__ = 'Time'
    default_error_messages = {
        ERROR_TYPE.invalid: "A valid timestamp is required but got type: {input_type}"
    }
    datetime_parser = datetime.datetime.strptime
    datetime_formatter = datetime.datetime.strftime

    def __init__(self, default_value, required,
                 description, out_format: str = None, in_format: str = None, *args, **kwargs):
        super().__init__(default_value, required, description, *args, **kwargs)

        self.in_format = in_format
        self.out_format = out_format

    def get_column_type(self):
        return "TIME"

    def get_type(self):
        return "time"

    def serialize(self, value: any) -> str:
        if not value or isinstance(value, str):
            return value

        if self.out_format is None:
            return str(value)

        assert isinstance(value, datetime.time), 'TypeError: value must datetime.time object'

        return value.strftime(self.out_format)

    def deserialize(self, value: any) -> datetime.time:
        if not value or isinstance(value, datetime.time):
            return value

        try:
            parsed = self.datetime_parser(value, self.in_format)
        except (ValueError, TypeError):
            self.fail(ERROR_TYPE.invalid, input_type=type(value))
        else:
            return parsed.time()


class Date(RpcType):
    __rpc_tag__ = "DT"
    default_error_messages = {
        ERROR_TYPE.invalid: "A valid date is required but got type: {input_type}",
    }

    datetime_parser = datetime.datetime.strptime

    def __init__(self, default_value, required, description, in_format=None, out_format=None, *args, **kwargs):

        super().__init__(default_value, required, description, *args, **kwargs)

        self.input_format = in_format
        self.out_format = out_format

    def get_column_type(self):
        return "Date"

    def get_type(self):
        return "date"

    def serialize(self, value: any) -> str:
        if not value or isinstance(value, str):
            return value

        if self.out_format is None:
            return str(value)

        assert isinstance(value, datetime.date), 'TypeError: value must `datetime.date`'
        return value.strftime(self.out_format)

    def deserialize(self, value: any) -> datetime.date:
        if isinstance(value, datetime.datetime):
            self.fail(ERROR_TYPE.invalid, input_type=type(value))

        if isinstance(value, datetime.date):
            return value

        try:
            parsed = self.datetime_parser(value, self.input_format)
        except (ValueError, TypeError):
            self.fail(ERROR_TYPE.invalid, input_type=type(value))
        else:
            return parsed.date()


class DateTime(RpcType):
    __rpc_tag__ = "DTT"
    default_error_messages = {
        ERROR_TYPE.invalid: "A valid datetime is required but got type: {input_type}"
    }
    datetime_parser = datetime.datetime.strptime

    def __init__(self, default_value, required, description, out_format=None,
                 in_format=None, default_timezone=None, *args, **kwargs):
        super().__init__(default_value, required, description, *args, **kwargs)

        self.out_format = out_format
        self.in_format = in_format
        self.timezone = default_timezone

    def get_column_type(self):
        return "DateTime"

    def get_timezone(self):
        return self.timezone or pytz.timezone('UTC')

    def get_type(self):
        return "datetime"

    def serialize(self, value: datetime.datetime) -> str:
        if not value or isinstance(value, str):
            return value

        if not self.out_format:
            return str(value)

        try:
            return value.strftime(self.out_format)
        except (ValueError, TypeError):
            self.fail(ERROR_TYPE.invalid, input_type=type(value))

    def deserialize(self, value: any) -> datetime.datetime:
        if isinstance(value, (datetime.date, datetime.time)):
            self.fail(ERROR_TYPE, input_type=type(value))

        if isinstance(value, datetime.datetime):
            return value.astimezone(self.get_timezone())

        try:
            parsed = self.datetime_parser(value, self.in_format)
            return parsed.astimezone(self.get_timezone())
        except (ValueError, TypeError):
            self.fail(ERROR_TYPE.invalid, input_type=type(value))


class Float(RpcType):
    __rpc_tag__ = "F"
    default_error_messages = {
        ERROR_TYPE.invalid: 'A valid number is required but get type: {input_type}',
    }

    def get_type(self):
        return "float"

    def get_column_type(self):
        return "Float"

    def deserialize(self, value: any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            self.fail(ERROR_TYPE.convert, input_type=type(value))

    def serialize(self, value: any) -> float:
        return float(value)


class Double(Float):
    __rpc_tag__ = "DB"
    default_error_messages = {
        ERROR_TYPE.invalid: "A valid double number is required but get type: {input_type}"
    }

    def get_type(self):
        return "double"

    def get_column_type(self):
        return "Float"


class String(RpcType):
    __rpc_tag__ = "S"
    default_error_messages = {
        ERROR_TYPE.invalid: 'Not a valid string get type: {input_type}',
        ERROR_TYPE.convert: 'Type: {input_type} not support convert to `str`'
    }

    def get_type(self):
        return "string"

    def valid(self, name: str, value=None):
        if self.required and value is None:
            raise ValidationError(msg=" %s is required, but value is %s" % (name, value))

        if value is not None and not type(value).__name__ == "str":
            raise self.fail("invalid", input_type=type(value).__name__)

    def get_column_type(self):
        return "String"

    def serialize(self, value: any) -> any:
        return str(value)

    def deserialize(self, value: any) -> any:
        if value is None:
            return value

        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            self.fail(ERROR_TYPE.convert, input_type=type(value))
        return str(value)


class List(RpcType):
    __rpc_tag__ = "L"
    default_error_messages = {
        ERROR_TYPE.invalid: 'Expected a list of items but get type: {input_type}.',
    }

    def __init__(self, elem_type: RpcType, required: bool, description: str = "",
                 validator: Validate = None, validate_extractor=None, origin: str = None):
        RpcType.__init__(self, None, required, description,
                         validator=validator, validate_extractor=validate_extractor, origin=origin)
        self.elem = elem_type

    def get_type(self):
        return "list"

    def get_elem(self):
        return self.elem

    def valid(self, name: str, value: list):
        super().valid(name, value)
        for idx, elem in enumerate(value or []):
            try:
                self.elem.valid(name, elem)
            except ValidationError as exc:
                raise ValidationError(msg={"@index[%s]" % idx: exc.msg})

    def get_column_type(self):
        pass

    def serialize(self, value: any) -> list:
        if isinstance(value, str):
            value = json.loads(value)

        if not isinstance(value, list):
            self.fail(ERROR_TYPE.invalid, input_type=type(value))

        elem_list = []
        for idx, elem in enumerate(value or []):
            try:
                elem_list.append(self.elem.serialize(elem))
            except ValidationError as exc:
                raise ValidationError(msg={"@index[%s]" % idx: exc.msg})
        return elem_list

    def deserialize(self, value: any) -> list:
        if not isinstance(value, list):
            self.fail(ERROR_TYPE.invalid, input_type=type(value))

        elem_list = []
        for idx, elem in enumerate(value or []):
            try:
                elem_list.append(self.elem.deserialize(elem))
            except ValidationError as exc:
                raise ValidationError(msg={"@index[%s]" % idx: exc.msg})
        return elem_list


class Dict(RpcType):
    """
    复合类型，即字典或 Class
    """

    __rpc_tag__ = "D"
    default_error_messages = {
        ERROR_TYPE.invalid: 'Expected a dictionary of items but get type: {input_type}',
    }

    def __init__(self, required: bool, description: str = "", origin: str = None, **kwargs):
        validator = kwargs.pop("validator", None)
        validate_extractor = kwargs.pop("validate_extractor", None)
        RpcType.__init__(self, None, required=required, description=description, origin=origin,
                         validator=validator, validate_extractor=validate_extractor)

        self.type_dict: typing.Dict[str, RpcType] = {}
        self.type_dict.update(kwargs)

    def add_field(self, name: str, type_info: RpcType):
        """
        为复合类型添加字段信息
        :param name:
        :param type_info:
        :return:
        """
        self.type_dict[name] = type_info

    def get_type(self):
        return "dict"

    def get_elem_info(self) -> typing.Dict[str, RpcType]:
        """
        获取字段信息
        :return:
        """
        return self.type_dict

    def valid(self, name: str, value: dict):
        super().valid(name, value)

        if self.required is False and value is None:
            return

        _error = {}
        for key, type_def in self.type_dict.items():
            val = value.get(key, None)
            try:
                type_def.valid(key, val)
            except ValidationError as exc:
                _error[key] = exc.msg

        if _error:
            raise ValidationError(msg=_error)

    def get_column_type(self):
        pass

    def serialize(self, value: any) -> dict:
        if not isinstance(value, dict):
            self.fail(ERROR_TYPE.invalid, input_type=type(value))

        data, _error = {}, {}
        for key, type_def in self.type_dict.items():
            val = value.get(key, None)
            try:
                data[key] = type_def.serialize(val)
            except ValidationError as exc:
                _error[key] = exc.msg

        if _error:
            raise ValidationError(msg=_error)
        return data

    def deserialize(self, value: any) -> dict:
        if not isinstance(value, dict):
            self.fail(ERROR_TYPE.invalid, input_type=type(value))

        data, _error = {}, {}
        for key, type_def in self.type_dict.items():
            val = value.get(key, None)
            try:
                data[key] = type_def.deserialize(val)
            except ValidationError as exc:
                _error[key] = exc.msg

        if _error:
            raise ValidationError(msg=_error)
        return data


class Enum(RpcType):
    __rpc_tag__ = "E"

    default_error_messages = {
        ERROR_TYPE.invalid: 'Expected a enumeration of items but get type: {input_type}',
    }

    def __init__(self, name: str, default_value, required: bool, description: str = "", origin: str = None, **kwargs):
        validator = kwargs.pop("validator", None)
        validate_extractor = kwargs.pop("validate_extractor", None)
        RpcType.__init__(self, default_value, required=required, description=description,
                         validator=validator, validate_extractor=validate_extractor, origin=origin)

        self.name = name
        self.enum_dict: typing.Dict[str, RpcType] = {}
        self.rpc_type: typing.Union[RpcType, None] = None
        for key, value in kwargs.items():
            if self.rpc_type is None:
                self.set_rpc_type(value)

            self.enum_dict[key] = value

    def set_rpc_type(self, v: RpcType):
        self.rpc_type = copy.deepcopy(v)
        self.rpc_type.default_value = self.default_value
        self.rpc_type.description = self.description
        self.rpc_type.required = self.required

    def item_value(self, item_name: str) -> typing.Any:
        """
        获取当前枚举的 item_name 项的值
        """
        item = self.enum_dict.get(item_name)
        if not item:
            raise KeyError(f"枚举类型 {self.name} 不存在 {item_name} 项")

        return item.default_value

    def add_item(self, key: str, e: RpcType):
        if self.rpc_type is None:
            self.set_rpc_type(e)

        if self.rpc_type.__rpc_tag__ != e.__rpc_tag__:
            raise AssertionError(
                f"Can not add different type as enumeration's item, already got "
                f"{self.rpc_type}, and receive new one with type {type(e)}"
            )

        self.enum_dict[key] = e

    def get_type(self):
        return "enum"

    def get_column_type(self):
        """
        枚举的类型取决于其元素类型
        """
        return self.rpc_type.get_column_type()

    def serialize(self, value: any) -> dict:
        if not value:
            return value
        try:
            return self.rpc_type.serialize(value)
        except ValidationError:
            self.fail(ERROR_TYPE.invalid, input_type=type(value))

    def deserialize(self, value: any) -> any:
        if not value:
            return value

        try:
            return self.rpc_type.deserialize(value)
        except ValidationError:
            self.fail(ERROR_TYPE.invalid, input_type=type(value))


base_tags = ["B", "I", "DT", "DTT", "F", "V", "DB", "S"]
numeric_tags = ["I", "F", "DB"]


def _check_tag(t: RpcType, tag: str) -> bool:
    return getattr(t, "__rpc_tag__", "") == tag


def is_base_type(t: RpcType) -> bool:
    return getattr(t, "__rpc_tag__", None) in base_tags


def is_list(t: RpcType) -> bool:
    return _check_tag(t, "L")


def is_dict(t: RpcType) -> bool:
    return _check_tag(t, "D")


def is_numeric(t: RpcType) -> bool:
    return getattr(t, "__rpc_tag__", None) in numeric_tags


def is_int(t: RpcType) -> bool:
    return getattr(t, "__rpc_tag__", None) == "I"


def is_float(t: RpcType) -> bool:
    return getattr(t, "__rpc_tag__", None) == "F"


def is_string(t: RpcType) -> bool:
    return _check_tag(t, "S")


def is_boolean(t: RpcType) -> bool:
    return _check_tag(t, "B")


def is_enum(t: RpcType) -> bool:
    return _check_tag(t, "E")
