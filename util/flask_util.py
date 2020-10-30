from flask import Flask
from flask_restplus import Swagger, Api


def init_api_doc(app: Flask, api: Api):
    """
    初始化 Flask 的文档信息，主要是 Flask 中 Resource 的 url 参数信息，
    必须经过此函数初始化后才能够正常获取
    """
    sw = Swagger(api)
    with app.app_context():
        for ns in sw.api.namespaces:
            for resource, urls, kwargs in ns.resources:
                for url in urls:
                    _ = sw.serialize_resource(ns, resource, url, kwargs)
