#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

__author__ = 'wujing'

import asyncio
import logging
import aiomysql

def log(sql, args = ()):
    logging.info('SQL: %s' % sql)

async def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host = kw.get('host', 'lochalhost'),
        port = kw.get('port', 3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('charset', 'utf=8'),
        autocommit = kw.get('autocommit', True),
        maxsize = kw.get('maxsize', 10),
        minsize = kw.get('minsize', 1),
        loop = loop
    )

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
    log(sql)
    with (await __pool) as conn:
        try:
            cur = await conn.cursor()
            await cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return affected

class Field(object):

    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

class IntegerField(Field):

    def __init__(self, name = None, name = None, column_type = 'bigint', primary_key = False, default = None):
        super().__init__(name, column_type, primary_key, default)

class StringField(Field):

    def __init__(self, name = None, primary_key = False, default = None, ddf = 'varchar(100)'):
        super().__init__(name, ddf, primary_key, default)

class ModelMetaclass(type):

    def __new__(cls, name, bases, attrs):
        # except Model itself
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        # get table name
        table_name = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, table_name))
        # get all the Field and primary_key
        mappings = dict()
        fields = []
        primary_key = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info(' found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    # find primary_key
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
        attrs['__select__'] = 'select `%s`, `%s` from `%s`' % (
                                            primary_key, 
                                            ', '.join(escaped_fields),
                                            table_name
        )
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (
                                            table_name,
                                            ', '.join(escaped_fields),
                                            primary_key,
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

    def get_value(self, key):
        return getattr(self, key, None)

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
    async def find(cls, pk):
        'find object by primary key.'
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

class User(Model):
    __table__ = 'user'

    id = IntegerField(primary_key = True)
    name = StringField()