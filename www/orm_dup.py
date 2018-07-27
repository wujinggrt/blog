#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

__author__ = 'wujing'

import re
import sys
import asyncio
import logging; logging.basicConfig(level=logging.INFO)
import aiomysql

def log(sql, args = None):
    logging.info('SQL: %s, args: %s' % (sql, args or 'No params'))

async def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host = kw.get('host', 'localhost'),
        port = kw.get('port', 3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('charset', 'utf8'),
        autocommit = kw.get('autocommit', True),
        maxsize = kw.get('maxsize', 10),
        minsize = kw.get('minsize', 1),
        loop = loop
    )

async def destroy_pool():
    global __pool
    if __pool is not None:
        __pool.close()
        await __pool.wait_closed()

# sql is a str type, args is a list.
# returns a list type.
async def select(sql, args, size=None):
    log(sql, args)
    global __pool
    with (await __pool) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = await cur.fetchmany()
        else:
            rs = await cur.fetchall()
        logging.info('rows returned: %s' % len(rs))
        return rs

async def execute(sql, args, size=None):
    log(sql, args)
    with (await __pool) as conn:
        try:
            cur = await conn.cursor()
            await cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return affected

 
# 这个函数主要是把查询字段计数 替换成sql识别的?
# 比如说：insert into  `User` (`password`, `email`, `name`, `id`) values (?,?,?,?)  看到了么 后面这四个问号
def create_args_string(num):
    lol=[]
    for n in range(num):
        lol.append('?')
    return (','.join(lol))

class Field(object):

    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        # 返回 表名字 字段名 和字段类型
        return "<%s , %s , %s>" %(self.__class__.__name__, self.name, self.column_type)

class IntegerField(Field):

    def __init__(self, name = None, column_type = 'int', primary_key = False, default = None):
        super().__init__(name, column_type, primary_key, default)

class StringField(Field):

    def __init__(self, name = None, column_type='varchar(100)', primary_key = False, default = None):
        super().__init__(name, column_type, primary_key, default)

class BooleanField(Field):

    def __init__(self, name=None, column_type='Boolean', primary_key=False, default=None):
        super().__init__(name, column_type, primary_key, default)

class FloatField(Field):

    def __init__(self, name=None, column_type='float', primary_key=False, default=None):
        super().__init__(name, column_type, primary_key, default)

class TextField(Field):

    def __init__(self, name=None, column_type='text', primary_key=None, default=None):
        super().__init__(name, column_type, primary_key, default)

class ModelMetaclass(type):

    def __new__(cls, name, bases, attrs):
        # except Model itself
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        # get table name
        # __table__ is defined in subclass User as a class field.
        table_name = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, table_name))
        # get all the Field and primary_key
        mappings = dict()
        # all keys but primary key
        fields = []
        primary_key = None
        # key vallue
        # save keys and fields in __fields__ but subclass
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info(' found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    # find more than one primary_key, it should not happened.
                    if primary_key:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primary_key = k
                else:
                    fields.append(k)
        if not primary_key:
            raise RuntimeError('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        # store the relation between attrs and columns
        attrs['__mappings__'] = mappings
        attrs['__table__'] = table_name
        # primary key name
        attrs['__primary_key__'] = primary_key
        # other name
        attrs['__fields__'] = fields
        # construct default SELECT, INSERT, UPDATE and DELETE phrase
        # sql use the `` symbol to sign variable
        # the later work is to pass parameters to the attrs. These phrase then carries out.
        # And '?' will be replace
        # the second %s dose not use `` because escaped_fields (escqped means ``) are all surrounded by ``.
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (
                                            primary_key, 
                                            ', '.join(escaped_fields),
                                            table_name
                                        )
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (
                                            table_name,
                                            ', '.join(escaped_fields),
                                            primary_key,
                                            # plus primary key.
                                            create_args_string(len(escaped_fields) + 1)
                                        )
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (
                                            table_name,
                                            ', '.join(
                                                map(
                                                    lambda f: '`%s`=?' % (
                                                        mappings.get(f).name or f
                                                    ), 
                                                    fields
                                                )
                                            ),
                                            primary_key
                                        )
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (
                                            table_name,
                                            primary_key
                                        )  
        return type.__new__(cls, name, bases, attrs)

class Model(dict, metaclass = ModelMetaclass):

    def __init__(self, **kw):
        super().__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    # supported by dict
    # key-value type as arguments pass to this class type object,
    # then return it's values by this methods.
    def get_value(self, key):
        return getattr(self, key, None)
        
    # fields in Object Field,
    # such like created_at, user_id
    def get_value_or_default(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    # 类方法有类变量cls传入，从而可以用cls做一些相关的处理。并且有子类继承时，调用该类方法时，传入的类变量cls是子类，而非父类。
    async def find_all(cls, where=None, args=None, **kw):
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
 
        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        # dict 提供get方法 指定放不存在时候返回后学的东西 比如a.get('Fuck',None)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) ==2:
                sql.append('?,?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value : %s ' % str(limit))
 
        rs = await select(' '.join(sql),args) #返回的rs是一个元素是tuple的list
        return [cls(**r) for r in rs]  # **r 是关键字参数，构成了一个cls类的列表，其实就是每一条记录对应的类实例
    
    @classmethod
    @asyncio.coroutine
    def findNumber(cls, selectField, where=None, args=None):
        '''find number by select and where.'''
        sql = ['select %s __num__ from `%s`' %(selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = yield from select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['__num__']

    @classmethod
    async def find(cls, pk):
        'find object by primary key.'
        print('%s where `%s`=%s' % (
                            cls.__select__, 
                            cls.__primary_key__,
                            pk)
                            )
        rs = await select('%s where `%s`=?' % (
                            cls.__select__, 
                            cls.__primary_key__),
                            [pk],
                            1
                        )
        if len(rs) == 0:
            return None
        return cls(**rs[0])
    
    async def save(self):
        args = list(
            map(
                self.get_value_or_default,
                self.__fields__
            )
        )
        args.append(self.get_value_or_default(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)

    async def update(self):
        args = list(map(self.get_value, self.__fields__))
        args.append(self.get_value(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update record: affected rows: %s'%rows)

    # update some of rows
    async def update_some(self):
        # get the valid args
        # dict store by hash, so it is not always in order.
        # each time field(key) replace in sql, corresponding values store in list,
        # so that the order fits ok.
        # first rows is keys, second is vallues.
        fields_mappings = {k: self.get_value(k) for k in self.__fields__ if self.get_value(k)}
        sql_args = list(fields_mappings.items())
        sql_keys, sql_values = list(zip(*sql_args))
        sql_keys, sql_values = list(sql_keys), list(sql_values)
        sql = 'update `%s` set %s where `%s`=?' % (
                    self.__table__,
                    ', '.join(
                        map(
                            lambda f: '`%s`=?' % (
                                self.__mappings__.get(f).name or f
                            ),
                            sql_keys
                        )
                    ),
                    self.__primary_key__
                )
        sql_values.append(self.get_value(self.__primary_key__))
        rows = await execute(sql, sql_values)
        if rows != 1:
            logging.warn('failed to update_some record: affected rows: %s'%rows)

    async def delete(self):
        args = [self.get_value(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to delete by primary key: affected rows: %s' %rows)

if __name__ == '__main__':
    # each user is a new object.
    class User(Model):
        __table__ = 'user'

        # id = IntegerField(primary_key = True)
        # name = StringField()

        id = IntegerField('id',primary_key=True) #主键为id， tablename为User，即类名
        name = StringField('name')
        email = StringField('email')
        password = StringField('password')

    loop = asyncio.get_event_loop()

    # create instance
    async def test(loop):
        await create_pool(
            loop = loop, 
            host = '127.0.0.1', 
            port = 3306,
            user = 'root',
            password = 'wujing',
            db = 'test'
        )
        user = User(id=2, name='Tom', email='wujing@gmail.com', password='12345')
        await user.save()
        r = await user.find(2)
        print(r)
        await destroy_pool()

    loop.run_until_complete(test(loop))
    loop.close()