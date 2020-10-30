"""
提供 RPC 服务接口的基类，所有的接口通过继承 Context 基类，隐藏其具体 RPC 实现，
及通过基类提供基础类库的基础封装功能
"""

import typing

from ..logger import Logger
from ..trace import TraceInfo
from .cache import ContextCache
from ..pool.host_info import HostInfo


def _empty() -> typing.Union['Context', None]:
    return None


class Context(object):
    """
    上下文类，记录了当前调用的各种信息，如当前关联的 RPC 服务及其调用状况,
    """
    def __init__(self, trace_info: TraceInfo = None,
                 prev: typing.Union[typing.Callable[[], typing.Union['Context', None]], None] = None,
                 client_cache: ContextCache = None,
                 servicer_cache: ContextCache = None,
                 logger=None,
                 impl_context=None,
                 host: typing.Union[HostInfo, None] = None):
        """
        构建一个上下文对象， trace_info 用于记录调用状况，
        prev 是当前上下文的上一级上下文，用于关联多个调用
        cache 是上下文的缓存管理器，一般只有库开发人员会使用
        当没有传递 trace_info, 但传递了 prev 时， 会使用 prev 的 trace_info 来构建新一级的 trace_info
        impl_context 是服务具体实现的上下文，他的具体类型由实现框架决定
        TODO: 考虑为服务具体上下文增加基础接口定义
        :param trace_info:
        :param prev:
        :param host:
        """
        # 上下文的前一个节点, 可通过获取上一个节点的 trace_info 来组织调用信息
        self._client_cache = client_cache
        self._servicer_cache = servicer_cache
        if not prev:
            prev = _empty
        self._prev: typing.Callable[[], typing.Union[Context, None]] = prev
        self._trace_info = trace_info
        self._logger = logger
        self._impl_context = impl_context
        self._host = host

    @property
    def logger(self) -> typing.Union[Logger, None]:
        """
        获取日志记录接口
        """
        if self._logger():
            return self._logger()

        prev = self._prev()
        if prev:
            return prev.logger

        return None

    @property
    def trace_info(self) -> TraceInfo:
        return self._trace_info

    def call(self, impl_name: str, action_name: str, args, identity: str = ""):

        """
        对 get_impl 的简易封装, 便于客户端调用, 获取客户端实现类,
        host 用于指定调用的服务地址, 不传递时将使用服务发现来查找服务地址
        identity 作为构建缓存及服务发现的标识符，当不传递时，使用 impl_name 作为标识，
        :param identity
        :param impl_name:
        :param action_name:
        :param args:
        :return:
        """
        impl = self.get_client_impl(impl_name, action_name, self._host, identity)
        return impl(args)

    def get_callable(self, impl_name: str, action_name: str, identity: str = "", host: HostInfo = None):
        """
        获取 Impl 的 Action，可用于直接调用，同时可从 Action 中得到
        具体的调用信息, 如 ConnectionInfo 等
        """
        return self.get_client_impl(impl_name, action_name, host or self._host, identity)

    def reg_client_impl(self, impl_name: str, impl):
        prev = self._prev()
        if prev:
            prev.reg_client_impl(impl_name, impl)
        else:
            self._client_cache.set(impl_name, impl)

    def reg_servicer_impl(self, impl_name: str, impl):
        prev = self._prev()
        if prev:
            prev.reg_servicer_impl(impl_name, impl)
        else:
            self._servicer_cache.set(impl_name, impl)

    def get_client_impl(
            self, impl_name: str,
            action_name: str,
            host: HostInfo = None,
            identity: str = ""):
        prev = self._prev()
        if prev:
            impl = prev.get_client_impl(impl_name, action_name, host or self._host, identity)
            return impl

        return self._client_cache.get(impl_name, action_name, host or self._host, identity)

    def get_servicer_impl(self, impl_name: str, action_name: str):
        prev = self._prev()
        if prev:
            impl = prev.get_servicer_impl(impl_name, action_name)
            return impl

        return self._servicer_cache.get(impl_name, action_name)


# Context 弱引用的声明
WeakContext = typing.Callable[[], typing.Union[None, Context]]
