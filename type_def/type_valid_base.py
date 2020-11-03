import weakref
import typing
from collections import namedtuple

from .type_error import ValidationError


def empty_weak():
    return None


VALID_TYPE = namedtuple("VALID_TYPE", ["null", "invalid"])("null", "invalid")

WeakRpcType = typing.Callable[[], typing.Union[None, typing.Any]]


class Validate(object):
    __validate__ = True

    default_error_messages = {
        VALID_TYPE.null: "Must support a value is not None",
    }

    def __init__(self):
        self.host: WeakRpcType = empty_weak
        self.error_messages = {}
        self.collection_err_msg()

    def valid(self, v: any):
        raise NotImplementedError

    def gen_invalid(self) -> any:
        raise NotImplementedError

    def fail(self, key, **kwargs):
        return fail(self, key, **kwargs)

    def set_host(self, host: typing.Any):
        self.host: WeakRpcType = weakref.ref(host)

    def collection_err_msg(self):
        # Collect default error message from self and parent classes
        messages = {}
        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, 'default_error_messages', {}))
        self.error_messages = messages


class EmptyValidate(Validate):
    """
    Default Validator for those type without validate configure
    """

    def valid(self, v: any):
        return None

    def gen_invalid(self) -> any:
        return None


def fail(validator, key, **kwargs):
    try:
        msg = validator.error_messages[key]
    except KeyError:
        class_name = validator.__class__.__name__
        msg = (
            'ValidationError raised by `{class_name}`, but error key `{key}` does '
            'not exist in the `error_messages` dictionary.'
        ).format(class_name=class_name, key=key)
        raise ValidationError(msg)
    message_string = msg.format(**kwargs)
    raise ValidationError(message_string)
