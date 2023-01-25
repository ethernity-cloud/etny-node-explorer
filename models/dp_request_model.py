import sys, os
from models.base_model import BaseModel

class DPRequestModel(BaseModel):
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

