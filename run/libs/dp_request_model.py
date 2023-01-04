
class DPRequestModel:
    """DPRequestModel"""
    fields = [
        'dpRequestId',
        'dproc',
        'cpuRequest',
        'memoryRequest',
        'storageRequest',
        'bandwidthRequest',
        'duration',
        'minPrice',
        'status',
        'createdAt',
    ]

    def __init__(self, arr) -> None:
        for index, key in enumerate(self.fields):
            try:
                setattr(self, key, arr[index])
            except IndexError:
                pass
        self.id = self.dpRequestId + 1 # pylint: disable=no-member,invalid-name

    @property
    def keys(self):
        """property keys"""
        return ['id', *self.fields]

    @property
    def items(self) -> dict:
        """property items"""
        return {x: getattr(self, x) for x in dir(self) if x in ['id', *self.fields]}
