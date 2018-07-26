
#### sql
```py
attrs['__select__']='select `%s`, %s from `%s` '%(primaryKey,', '.join(escaped_fields), table_name)
attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s) ' %(table_name, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields)+1))
attrs['__update__']='update `%s` set %s where `%s` = ?' % (table_name, ', '.join(map(lambda f:'`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
attrs['__delete__']='delete from `%s` where `%s`=?' %(table_name, primaryKey)


select('%s where `%s`=?' %(cls.__select__, cls.__primary_key__), [primarykey], 1)

args = list(map(self.getValueOrDefault, self.__fields__))
print('save:%s' % args)
args.append(self.getValueOrDefault(self.__primary_key__))
execute(self.__insert__, args)

#获得的value是User2实例的属性值，也就是传入的name，email，password值
args = list(map(self.getValue, self.__fields__)) 
args.append(self.getValue(self.__primary_key__))
rows = yield from execute(self.__update__, args)

args = [self.getValue(self.__primary_key__)]
rows = yield from execute(self.__delete__, args)
```

The rest of work is to passing parameter, then select/execute will perform it.  
All of args are list type.

#### note
Each User class means single indeendent infomation.

#### charset
AttributeError: 'Connection' object has no attribute '_writer'
```py
charset=kwargs.get('charset', 'utf8'),
```

#### authority
All operation related to mysql requires sudo.

#### privileges on mysql
my ```sudo python3```version is default on ubuntu rather than anaconda.  
As I have to get sudo privileges for connecting mysql, I found that using this phrase performs well.   
```sudo ~/anaconda/bin/python3 filename.py```
But script should not run as root. Mysql privileges should be opened.   
Attaching
```
[mysqld]
skip-grant-tables
```
to /etc/mysql/my.cnf. Then  
```
sudo service mysql restart
```
it works fine.

#### problem on create_pool
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on '127.0.0.1'")    
raise OSError(err, 'Connect call failed %s' % (address,))  
ConnectionRefusedError: [Errno 111] Connect call failed ('127.0.0.1', 9000)    
souce code:  
```py
 __pool = await aiomysql.create_pool(
        host = kw.get('host', 'lochalhost'), # wrongs in localhost
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
```
corrected but not works.  

error:
pymysql.err.InternalError: (1049, "Unknown database 'test'")  
It requires an existed database, so I need to create it.  
```sh
mysql> CREATE DATABASE test;
Query OK, 1 row affected (0.01 sec)

mysql> exit
Bye
wujing@ubuntu:~/Desktop/wujinggrt/www$ python3 dup.py 
wujing@ubuntu:~/Desktop/wujinggrt/www$ python3 dup.py 
wujing@ubuntu:~/Desktop/wujinggrt/www$ 
```
it works.  

#### models done
results:
```sh
wujing@ubuntu:~/Desktop/wujinggrt/www$ python3 test_orm.py 
INFO:root:found model: User (table: users)
INFO:root: found mapping: id ==> <StringField , None , varchar(50)>
INFO:root: found mapping: email ==> <StringField , None , varchar(50)>
INFO:root: found mapping: password ==> <StringField , None , varchar(50)>
INFO:root: found mapping: admin ==> <BooleanField , None , Boolean>
INFO:root: found mapping: name ==> <StringField , None , varchar(50)>
INFO:root: found mapping: image ==> <StringField , None , varchar(500)>
INFO:root: found mapping: created_at ==> <FloatField , None , float>
INFO:root:found model: Blog (table: blogs)
INFO:root: found mapping: id ==> <StringField , None , varchar(50)>
INFO:root: found mapping: user_id ==> <StringField , None , varchar(50)>
INFO:root: found mapping: user_name ==> <StringField , None , varchar(50)>
INFO:root: found mapping: user_image ==> <StringField , None , varchar(500)>
INFO:root: found mapping: name ==> <StringField , None , varchar(50)>
INFO:root: found mapping: summary ==> <StringField , None , varchar(200)>
INFO:root: found mapping: content ==> <TextField , None , text>
INFO:root: found mapping: created_at ==> <FloatField , None , float>
INFO:root:found model: Comment (table: comments)
INFO:root: found mapping: id ==> <StringField , None , varchar(50)>
INFO:root: found mapping: blog_id ==> <StringField , None , varchar(50)>
INFO:root: found mapping: user_id ==> <StringField , None , varchar(50)>
INFO:root: found mapping: user_name ==> <StringField , None , varchar(50)>
INFO:root: found mapping: user_image ==> <StringField , None , varchar(500)>
INFO:root: found mapping: content ==> <TextField , None , text>
INFO:root: found mapping: created_at ==> <FloatField , None , float>
INFO:root:create database connection pool...
INFO:root:SQL: insert into `users` (`email`, `password`, `admin`, `name`, `image`, `created_at`, `id`) values (?,?,?,?,?,?,?)
```
    