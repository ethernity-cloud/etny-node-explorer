from datetime import datetime


class Node:
    
    __private_fields = ['id', 'order_id', 'created_on', 'last_updated', 'updates_count']

    all_fields = [
        'id',
        'order_id',
        'address',
        'cpu',
        'memory',
        'storage',
        'bandwith',
        'duration',
        'status',
        'cost',
        'created_on',
        'last_updated',
        'updates_count'
    ]

    def __init__(self, **kwargs):
        for field in self.all_fields:
            setattr(self, field, kwargs.get(field))

    def items(self):
        return list(x for x in dir(self) if type(getattr(self, x)) in [int, str, float])

    def __str__(self) -> str:
        return str([x for x in dir(self) if not x.startswith('_')])

    def instance(self):
        return {x: getattr(self, x) for x in dir(self) if not x.startswith('__') and type(getattr(self, x)) in [int, str, float]}
    
    def public(self):
        return {x: y for x,y in self.instance().items() if x not in self.__private_fields}

    def private(self):
        return {x: y for x,y in self.instance().items() if x in self.__private_fields}

    def getAttr(self, row):
        value = getattr(self, row)
        try:
            if row in ['created_on', 'last_updated'] and value:
                return datetime.fromtimestamp(value).strftime('%d-%m-%Y %H:%M')
            if row == 'id' and value == -1:
                return 0
            raise Exception
        except Exception as e:
            return value
        
            

