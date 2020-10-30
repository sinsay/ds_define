from ..pool import Pool
from ..pool.host_info import HostInfo
from .callable_impl import CallableImpl, CallableAction


class ContextCache(object):
    def __init__(self, pool: Pool = None):
        # 当前上下文使用的连接管理器
        self.pool = pool
        # 上下文已注册的服务, 这些服务只会存在于 root 中
        self.servicer_map = {}
        # 当前上下文所使用的 rpc 服务缓存, Value 为 CallableImpl
        self.servicer_cache = {}

    def get(self, impl_name: str, action_name: str, host: HostInfo = None, identity: str = str) -> CallableAction:
        """
        获取一个已注册的服务, 及其对应的 action, 可以通过指定 host 的方式，来强制调用 host 指定的 impl 服务
        identity 作为缓存的标识符，如果没有传递，则使用 impl_name 作为缓存标识符
        """
        identity = identity or impl_name
        callable_impl: CallableImpl = self.servicer_cache.get(impl_name)
        if not callable_impl:
            impl = self.servicer_map.get(impl_name)
            if not impl:
                raise KeyError("can not find servicer named %s" % impl_name)

            callable_impl: CallableImpl = self.build_cache(identity, impl, host)

        if not callable_impl.has_action(action_name):
            raise KeyError("can not find action named %s in servicer %s" % (impl_name, action_name))

        return CallableAction(callable_impl, action_name)

    def set(self, impl_name: str, impl):
        """
        注册一个服务
        :param impl_name:
        :param impl:
        :return:
        """
        self.servicer_map[impl_name] = impl

    def build_cache(self, identity: str, impl_class, host: HostInfo = None) -> CallableImpl:
        """
        为当前服务构建缓存信息，缓存信息为该服务将使用的链接等信息, 当传递了 host 时，使用 host 提供的 Connection
        :param identity:
        :param impl_class:
        :param host
        :return:
        """
        # 如果传递了 host, 则优先使用 host 提供的连接
        conn = host and host.get() or self.pool.get(identity)
        # TODO: 当需要统计信息时，从 CallableImpl 及此处做调整
        callable_impl = CallableImpl(impl_class, conn, self.pool)
        if not host:
            # 如果是来自客户端指定 Host 的，则不作缓存
            self.servicer_cache[identity] = callable_impl
        return callable_impl
