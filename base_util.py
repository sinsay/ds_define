rpc_impl_rename = "_rpc_impl_name"


def impl_name(name: str):
    """
    允许 RPC 服务的定义跟实现使用不同名称的类型
    :param name:
    :return:
    """
    def wrap(cls):
        setattr(cls, rpc_impl_rename, name)
        return cls

    return wrap
