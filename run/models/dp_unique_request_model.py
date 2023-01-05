
from models.base_model import BaseModel

class DPUniqueRequestModel(BaseModel):
    fields = [
        'id',
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
        'updated_at'
    ]
















