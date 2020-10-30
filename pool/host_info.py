"""
该文件用于配置接口或服务的主机信息，如 IP 端口，用户名等信息，
具体的是服务通过继承该类型来实现记录不同的信息
"""

from ..pool import ConnectionInfo


class HostInfo(object):
    def get(self) -> ConnectionInfo:
        raise NotImplemented("请使用指定实现的 HostInfo, 如 GRPCHostInfo")
