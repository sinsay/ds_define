from decimal import Decimal as _Decimal, DecimalException

from .type_def import *

from .type_valid import validator_constructor, StringValidate


class BigInteger(Integer):

    def get_column_type(self):
        return "BigInteger"


class SmallInteger(Integer):

    def get_column_type(self):
        return "SmallInteger"


class Char(String):
    default_error_messages = {
        ERROR_TYPE.invalid: "A valid char is required but get type: {input_type}"
    }

    def get_column_type(self):
        return "CHAR"


class Decimal(Double):

    def __init__(self, default_value, required: bool, description: str = "",
                 validator: Validate = None, validate_extractor=None, decimal_places=None,
                 rounding=None, *args, **kwargs):
        self.decimal_places = decimal_places
        self.rounding = rounding
        super().__init__(default_value, required, description, validator, validate_extractor, *args, **kwargs)

    def get_column_type(self):
        return "DECIMAL"

    def serialize(self, value: any) -> str:
        if isinstance(value, str):
            value = _Decimal(value.strip())

        if self.decimal_places:
            value = value.quantize(_Decimal('.1') ** self.decimal_places, rounding=self.rounding)

        return "{:f}".format(value)

    def deserialize(self, value: any) -> _Decimal:
        try:
            value = _Decimal(value)
        except DecimalException:
            self.fail(ERROR_TYPE.invalid)

        if self.decimal_places is None:
            return value
        return value.quantize(_Decimal('.1') ** self.decimal_places, rounding=self.rounding)


class Binary(String):
    default_error_messages = {
        ERROR_TYPE.invalid: 'A valid bytes is required but get type: {input_type}',
    }

    def get_column_type(self):
        return "Binary"


class LargeBinary(Binary):

    def get_column_type(self):
        return 'LargeBinary'


class Text(String):

    def get_column_type(self):
        return 'Text'


class Json(String):

    def get_column_type(self):
        return 'JSON'


def small_integer(description: str = "", required: bool = True,
                  minimum: int = None, maximum: int = None,
                  default_value: int = None) -> SmallInteger:
    """
    创建一个 SmallInteger 类型
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :return:
    """
    return SmallInteger(
        default_value, required, description,
        validator=validator_constructor(min=minimum, max=maximum)
    )


def big_integer(description: str = "", required: bool = True,
                minimum: int = None, maximum: int = None,
                default_value: int = None) -> BigInteger:
    """
    创建一个 BigInteger 类型
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :return:
    """
    return BigInteger(
        default_value, required, description,
        validator=validator_constructor(min=minimum, max=maximum)
    )


def decimal(description: str = "", required: bool = True,
            minimum: int = None, maximum: int = None,
            default_value: int = None) -> Decimal:
    """
    创建一个 Decimal 类型
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :return:
    """
    return Decimal(
        default_value, required, description,
        validator=validator_constructor(min=minimum, max=maximum)
    )


def binary(description: str = "", required: bool = True,
           min_length: int = None, max_length: int = None,
           default_value=None) -> Binary:
    """
    创建一个 二进制类型
    :param default_value:
    :param description:
    :param required:
    :param min_length:
    :param max_length:
    :return:
    """

    if min_length is not None and max_length is not None:
        validator = StringValidate(min_length=min_length, max_length=max_length)
    else:
        validator = None

    return Binary(
        default_value, required, description,
        validator=validator
    )


def large_binary(description: str = "", required: bool = True,
                 min_length: int = None, max_length: int = None,
                 default_value=None) -> Binary:
    """
    创建一个 长二进制类型
    :param default_value:
    :param description:
    :param required:
    :param min_length:
    :param max_length:
    :return:
    """

    if min_length is not None and max_length is not None:
        validator = StringValidate(min_length=min_length, max_length=max_length)
    else:
        validator = None

    return LargeBinary(
        default_value, required, description,
        validator=validator
    )


def char(description: str = "",
         required: bool = True,
         default_value=None) -> Char:
    """
    创建一个 字符 类型
    :param default_value:
    :param description:
    :param required:
    :return:
    """

    return Char(
        default_value, required, description,
        validator=StringValidate(min_length=1, max_length=1)
    )


def text(description: str = "",
         required: bool = True,
         default_value=None) -> Text:
    """
    创建一个 text 类型
    :param default_value:
    :param description:
    :param required:
    :return:
    """

    return Text(
        default_value, required, description,
        validator=StringValidate(min_length=1, max_length=1)
    )


def json(description: str = "",
         required: bool = True,
         default_value=None) -> Json:
    """
    创建一个 json 类型
    :param default_value:
    :param description:
    :param required:
    :return:
    """

    return Json(
        default_value, required, description,
        validator=StringValidate(min_length=1, max_length=1)
    )
