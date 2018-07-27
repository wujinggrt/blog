#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

__author__ = 'wujing'

import logging; logging.basicConfig(level = logging.INFO)

import asyncio
import os
import json
import time
import datetime
import orm

from aiohttp import web
from jinja2 import Environment
from jinja2 import FileSystemLoader
from coroweb import add_routes
from coroweb import add_static

async def logger_factory(app, handler):
    async def logger(request):
        logging.info('Request:%s %s' % (request.method, request.path))
        return (await handler(request))
    return logger

async def response_factory(app, handler):
    async def response(request):
        logging.info('Response handler...')
        r = await handler(request)
        # 如果相应结果为StreamResponse，直接返回
        # #treamResponse是aiohttp定义response的基类,即所有响应类型都继承自该类
        # StreamResponse主要为流式数据而设计
        if isinstance(r, web.StreamResponse):
            return r
        # 如果相应结果为字节流，则将其作为应答的body部分，并设置响应类型为流型
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        # 如果响应结果为字符串
        if isinstance(r, str):
            # 判断响应结果是否为重定向，如果是，返回重定向后的结果
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])  # 即把r字符串之前的"redirect:"去掉
            # 然后以utf8对其编码，并设置响应类型为html型
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        # 如果响应结果是字典，则获取他的jinja2模板信息，此处为jinja2.env
        if isinstance(r, dict):
            template = r.get('__template__')
            # 若不存在对应模板，则将字典调整为json格式返回，并设置响应类型为json
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                r["__user__"] = request.__user__  # 增加__user__,前端页面将依次来决定是否显示评论框
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        # 如果响应结果为整数型，且在100和600之间
        # 则此时r为状态码，即404，500等
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(r)
        # 如果响应结果为长度为2的元组
        # 元组第一个值为整数型且在100和600之间
        # 则t为http状态码，m为错误描述，返回状态码和错误描述
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        # 默认以字符串形式返回响应结果，设置类型为普通文本
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    #上面6个if其实只用到了一个，准确的说只用到了半个。大家可以把用到的代码找出来，把没有用到的注释掉，如果程序能正常运行，那我觉得任务也就完成了
    #没用到的if语句块了解一下就好，等用到了再回过头来看，你就瞬间理解了。
    return response


# def index(request):
    # return web.Response(body = b'<h1>WujingGrt</h1>', content_type = 'text/html')

@get('/')
def index(request):
    users = yield from User.find_all()
    return {
        '__template__': 'test.html',
        'users': users
    }

async def init(loop):
    app = web.Application(loop = loop)
    app.router.add_route('GET', '/', index)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()