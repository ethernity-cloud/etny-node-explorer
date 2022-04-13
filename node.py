from datetime import datetime


class Node:
    def __init__(self, no, address, cpu, mem, storage, band, duration, status, cost, first_timestamp, last_timestamp):
        self.no = no
        self.address = address
        self.cpu = cpu
        self.memory = mem
        self.storage = storage
        self.bandwith = band
        self.duration = duration
        self.status = status
        self.cost = cost
        self.created_on = first_timestamp
        self.last_updated = last_timestamp

    def print(self):
        print("No=", self.no, "address=", self.address, "created_on=", datetime.fromtimestamp(int(self.created_on)),
              "last_updated=", datetime.fromtimestamp(int(self.last_updated)))
