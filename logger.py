# -*- coding: utf-8 -*-

from logging import Logger as LoggerBase


class Logger(LoggerBase):
    """
    所有 logger 的基类，定义了日志记录的接口，所有的具体日志实现都继承自该接口,
    不再自定义基类，使用标准库的 Logger
    """
    pass
