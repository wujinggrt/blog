#!/usr/bin/env python3
# -*- coding: utf-8 -*-

' url handlers '

import re, time, json, logging, hashlib, base64, asyncio

# markdown2模块是一个支持markdown文本输入的模块，是Trent Mick写的开源模块，我们将其拷贝在本文件夹中，在这里调用
import markdown2  

from aiohttp import web

from coroweb import get, post
from apis import APIValueError, APIResourceNotFoundError, APIError, APIPermissionError, Page

from models import User, Comment, Blog, next_id
from config import configs

COOKIE_NAME = 'awesession'  # cookie名，用于设置cookie
_COOKIE_KEY = configs.session.secret  # cookie密钥，作为加密cookie的原始字符串的一部分

@get('/')
def index(request):
    users = yield from User.find_all()
    return {
        '__template__': 'test.html',
        'users': users
    }

