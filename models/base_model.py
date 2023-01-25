
from datetime import datetime
class BaseModel:
    fields = []
    def __init__(self, arr) -> None:
        for index, key in enumerate(self.fields):
            try:
                setattr(self, key, arr[index])
            except IndexError:
                pass
        self.id = self.dpRequestId + 1 # pylint: disable=no-member,invalid-name

    @property
    def keys(self) -> list:
        return list(set(['id', *self.fields]))

    @property
    def items(self) -> dict:
        return {x: getattr(self, x) for x in dir(self) if x in ['id', *self.fields]}

    def getAttr(self, row):
        value = getattr(self, row)
        try:
            if row in ['updated_at', 'createdAt'] and value:
                return datetime.fromtimestamp(value).isoformat()
            raise Exception
        except Exception:
            return value