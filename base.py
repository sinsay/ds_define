import typing

from .type_def.type_util import is_builtin_type
from .ctx import Context


class CommonAbs(object):
    """
    RPC 服务的抽象基类，所有需要提供 RPC 服务的类型都需要继承该类，

    """

    __rpc_tag__ = "__RPC_0X123__"

    def __init__(self, context: Context = None):
        self.context = context

    @staticmethod
    def same_rpc_thing(other):
        return getattr(other, '__rpc_tag__', "").startswith(CommonAbs.__rpc_tag__)


class CommonBase(CommonAbs):
    """
    RPC 服务定义的基类，在 RPC 服务的定义类中继承该类
    在代码生成阶段，该类负责支持解析获取服务的元信息，
    """

    __rpc_tag_base__ = "__RPC_0X123__456"

    @staticmethod
    def same_rpc_thing(other):
        return getattr(other, '__rpc_tag_base__', "") == CommonBase.__rpc_tag_base__


class CommonImpl(CommonAbs):
    """
    RPC 服务的实现类型, RPC 服务的具体实现类需要继承该类
    在运行阶段，该类负责组合生成好的 RPC 接口及其具体实现
    """
    __rpc_tag_impl__ = "__RPC_0X123__789"

    @staticmethod
    def same_rpc_thing(other):
        return getattr(other, '__rpc_tag_impl__', "") == CommonImpl.__rpc_tag_impl__


class RPCDict(object):
    """
    所有的服务接口的参数跟返回值都会继承该类型，从而得到序列化成 dict 的能力
    """

    def to_dict(self) -> dict:
        return convert2builtin(self.__dict__)

    def from_dict(self, _d: dict):
        return self

    def from_pb2(self, _context):
        return self

    @staticmethod
    def choose_default(f_from_ctx, default_value):
        """
        f_from_ctx 是从 Context 中读取的值, default_value 是配置在模型上的默认值
        当有配置默认值时将返回 default_value 否则返回 f_from_ctx
        """
        if default_value is not None:
            return default_value
        return f_from_ctx


def convert2builtin(obj) -> typing.Union[typing.Dict[str, typing.Any],
                                         typing.List,
                                         int, bool, float, str, None]:
    """
    转换任意复合类型到基础类型, deep_copy 决定了是否会进行深度拷贝，默认开启深度拷贝
    如果传递的类型不在支持的范围内则原样返回.
    WARN: 但如果一个类型无法转换为 builtin， 则说明他后续的序列化会出错。
    """

    d = obj

    if is_builtin_type(obj):
        return obj
    elif isinstance(obj, dict):
        d = dict()

        for key, value in obj.items():
            if key.startswith("_") or callable(value):
                continue

            if is_builtin_type(value):
                d[key] = value

            elif isinstance(value, (list, dict)):
                d[key] = convert2builtin(value)

            elif hasattr(value, "__dict__"):
                d[key] = convert2builtin(value.__dict__)
            else:
                d[key] = value

    elif isinstance(obj, list):
        d = []
        for i in obj:
            d.append(convert2builtin(i))

    elif hasattr(obj, "__dict__"):
        d = convert2builtin(obj.__dict__)

    return d
