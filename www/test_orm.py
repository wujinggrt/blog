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
        name = 'Test',
        email = 'test@qq.com',
        password = '123456',
        image = 'about:blank',
        admin = False
    )
    await u.save()
    await orm.destroy_pool()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()