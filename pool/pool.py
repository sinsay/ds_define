
class NoUsefulConnectionError(Exception):
    pass


class ConnectionInfo(object):
    """
    用于表示一个可复用的连接信息,
    该连接信息已包含了可使用的所有连接内容，调用
    get_conn 时，会根据当前策略给予返回可用的连接，
    当得到的连接不可用或出错时，可调用 useless 告知该
    ConnectionInfo，然后重新尝试 get_conn 获取可用的连接，
    当没有连接可用时，会抛出无连接可用的异常 NoUsefulConnectionError
    """
    def __init__(self, conn, meta=None):
        """
        conn 为具体的连接
        meta 为附加的数据
        """
        self.conn = conn
        self.meta = meta

    def __repr__(self):
        return f"ConnectionInfo({self.conn}, meta: {self.meta}"

    def get_conn(self):
        """
        获取连接的具体实现
        """
        return self.conn

    def useless(self):
        """
        报告当前连接已不可用
        """
        pass


class Pool(object):
    def get(self, key: str) -> ConnectionInfo:
        """
        获取一个连接信息
        """
        pass
