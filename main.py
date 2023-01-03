import asyncio, os
from web3 import Web3, __version__ as web3_version
from web3.middleware import geth_poa_middleware
from packaging import version
from config import config, Database, getLogger, Singleton
from multiprocessing import Process, Queue, Array
from functools import partial

logger = getLogger()
PROCESS_COUNT = 30


class DPRequestModel:
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
            except IndexError as e:
                pass
        self.id = self.dpRequestId + 1

    @property
    def keys(self):
        return ['id', *self.fields]

    @property
    def items(self) -> dict:
        return {x: getattr(self, x) for x in dir(self) if x in ['id', *self.fields]}


class BaseClass:
    def _baseConfig(self, contract = None) -> None:
        self._httpProvider = config['DEFAULT']['HttpProvider']
        self._contract = config['DEFAULT']['ContractAddress']
        self._indexFile = config['DEFAULT']['IndexFile']
        self._nodesFile = config['DEFAULT']['CSVFile']
        self._firstContractTX = config['DEFAULT']['firstContractTX']

        self._w3 = Web3(Web3.HTTPProvider(self._httpProvider))
        if version.parse(web3_version) < version.parse('5.0.0'):
            self._w3.middleware_stack.inject(geth_poa_middleware, layer=0)
        else:
            self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        self.etnyContract = contract if contract else self._get_etnyContract()
        
    def _get_etnyContract(self):
        return self._w3.eth.contract(address=self._contract, abi=self._get_contract_abi())

    def _get_contract_abi(self) -> str:
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/etnyContract.abi') as r:
                return r.read()
        except Exception as e:
            return None

    def run(self):
        pass

class InProcess(BaseClass, metaclass = Singleton):
    def __init__(self) -> None:
        super().__init__()
        self._baseConfig()
        print('init called....')

    def run(self, input, output, _max):
        try:
            for dp_request_id in iter(input.get, 'STOP'):
                _to = dp_request_id + PROCESS_COUNT
                for i in range(dp_request_id, _max + 1 if _max < _to else _to):
                    try:
                        item = self.etnyContract.caller()._getDPRequestWithCreationDate(i)
                        output.put(DPRequestModel([i, *item]))
                    except Exception as e:
                        print('---inline ',i, e)
                        continue
        except Exception as e:
            print('process error', e)

class GetDPRequests(BaseClass):
    def __init__(self) -> None:
        self._baseConfig()
        Database(config=config, logger = logger).init()

        self.init()


    def init(self):
        last_local_id = Database().getLastDPRequest()
        print('last_local_id = ', last_local_id)

        self.run(start_point=last_local_id if last_local_id else 0)

    def store(self, models):
        Database().storeDPRequests(models = models)

    def run(self, total = 0, start_point = 0, limit = 3):
        super().run()
        _total = total if total else self.etnyContract.functions._getDPRequestsCount().call()
        
        try:
            
            task_queue = Queue()
            done_queue = Queue()
            jobs = []
            _max = _total
            for i in range(PROCESS_COUNT):
                process = Process(target=InProcess().run, args=(task_queue, done_queue, _max))
                jobs.append(process)
                process.start()

            results = []
            for i in range(start_point, _max + 1, PROCESS_COUNT):
                print('i = ', i, len(results))
                task_queue.put(i)
                for res in range(PROCESS_COUNT if _max + 1 > start_point else (_max + 1) - start_point):
                    try:
                        result = done_queue.get(timeout=1)
                        results.append(result)
                    except Exception as e:
                        print('error = ', i, e)
                        continue

                if len(results) >= PROCESS_COUNT:
                    print('results = ', len(results))    
                    self.store(models = results)
                    results = []

            for i in results:
                self.store(models = results)
                print('results2 = ', len(results))
                results = []


            print('after loop')
            task_queue.put('STOP')
            task_queue.close()
            done_queue.close()
            for i in jobs:
                i.join()
                

        except Exception as e:
            print('global error', e)


if __name__ == '__main__':
    GetDPRequests()
    

    
