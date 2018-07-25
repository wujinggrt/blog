
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