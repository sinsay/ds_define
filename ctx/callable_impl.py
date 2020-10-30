"""
对 RPC Client 的浅包装，用于返回可调用的服务信息及其使用的其他关联信息，
如连接信息，连接池信息，调用状态等。
"""

import typing

from ..pool.pool import ConnectionInfo, Pool

# receive an impl_instance, action_name, and any additional args
# InvokeMethod = typing.Callable[[object, str, ...], any]
InvokeMethod = typing.Callable[..., any]


class CallableImpl(object):
    def __init__(self, impl_class, conn: ConnectionInfo, pool: Pool, statistic=None):
        """
        impl 是具体 RPC 的实现类，conn 是当前实现类使用的连接信息， pool 是该连接所在的
        连接池, statistic 是该服务的调用统计信息
        """
        self.impl = impl_class
        self.impl_instance = None
        self.conn = conn
        self.pool = pool
        self.statistic = statistic
        self.try_pool_again()

    def has_action(self, action: str):
        if not self.impl_instance:
            self.try_pool_again()
        return hasattr(self.impl_instance, action)

    def try_pool_again(self):
        """
        尝试从 Pool 中获取可用的连接信息
        """
        # GRPCConn 的 get_conn 本身使用了服务发现的策略，能够尝试切换连接
        if self.impl_instance:
            self.conn.useless()
        conn = self.conn.get_conn()
        self.impl_instance = self.impl(conn)

    def __call__(self, action: str, *args, **kwargs):
        """
        调用时才尝试去构建 Impl 类的实例，这样在调用失败时，客户端有机会在进行重试时
        调整 conn 跟 pool 的信息
        """

        invoke_method: InvokeMethod = kwargs.get("invoke_method")
        if invoke_method:
            kwargs.pop("invoke_method")
            return invoke_method(self.impl_instance, action, *args, **kwargs)
        else:
            return getattr(self.impl_instance, action)(*args, **kwargs)


class CallableAction(object):
    def __init__(self, impl: CallableImpl, action: str):
        self.impl: CallableImpl = impl
        self.action = action
        self.invoke: typing.Union[InvokeMethod, None] = None

    def set_invoke(self, invoke: InvokeMethod):
        self.invoke = invoke

    def __call__(self, *args, **kwargs):
        return self.impl(self.action, invoke_method=self.invoke,  *args, **kwargs)
