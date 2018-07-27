'test code'

import asyncio
import orm

from models import User
from models import Blog
from models import Comment

async def test(loop):
    await orm.create_pool(
        user = 'www-data',
        password = 'www-data',
        db = 'wujinggrt',
        loop = loop
    )
    u = User(
        id = '123',
        name = 'handsome guy',
        email = 'test@qq.com',
        password = '123456',
        image = 'about:blank',
        admin = False
    )

    b = Blog (
        id = '123',
        user_id = 'wujinggrt',
        user_name = 'wujing',
        user_image = 'about:blank',
        name = 'wu jing',
        summary = ' This is a simple summary!',
        content = "hello I'm going to write a long worlds",
    )
    
    rs = await b.save()
    print(rs)
    await orm.destroy_pool()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()