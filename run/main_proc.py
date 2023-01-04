import os
import sys
import signal
import time
from multiprocessing import Process, Queue
sys.path.extend([os.getcwd().split('/run')[0]])

# pylint: disable=wrong-import-position
from libs.base_class import BaseClass, config, getLogger, Singleton
from libs.db import DB
from libs.dp_request_model import DPRequestModel

logger = getLogger()
PROCESS_COUNT = 30

def signal_handler(sig, frame): # pylint: disable=unused-argument,redefined-outer-name
    """global error handling"""
    if len(GetDPRequests.results) > 0:
        print('resultsLen = ', len(GetDPRequests.results))
        GetDPRequests.store(models = GetDPRequests.results)
    sys.exit() 

for sig in [signal.SIGINT, signal.SIGTERM]:
    signal.signal(sig, signal_handler)

class InProcess(BaseClass, metaclass = Singleton):
    """process """
    def __init__(self, w3 = None, contract = None) -> None:
        super().__init__()
        self._baseConfig(w3 = w3, contract=contract)

    def run(self, _input, output, _max, _iter_count = 0): # pylint: disable=arguments-differ
        """run method"""
        try:
            for dp_request_id in iter(_input.get, 'STOP'):
                _to = dp_request_id + PROCESS_COUNT
                for i in range(dp_request_id, _max + 1 if _max < _to else _to):
                    try:
                        item = self.etnyContract.caller()._getDPRequestWithCreationDate(i) # pylint: disable=protected-access
                        output.put(DPRequestModel([i, *item]))
                    except Exception as err: # pylint: disable=broad-except
                        if 'Connection aborted' in str(err) and _iter_count < (PROCESS_COUNT):
                            time.sleep(.5)
                            return self.run(_input=_input, output=output, _max=_max, _iter_count=_iter_count + 1)
                        continue
        except Exception as err: # pylint: disable=broad-except
            print('process error', err)

class GetDPRequests(BaseClass):
    """main class"""
    results = []
    def __init__(self) -> None:
        self._baseConfig()
        DB(config=config, logger = logger).init()

        self.init()

    def init(self):
        """init method"""
        last_local_id = DB().get_last_dp_request()
        print('last_local_id = ', last_local_id)

        # self.get_missing_records()

        self.run(start_point=last_local_id if last_local_id else 0)

    @staticmethod
    def store(models):
        """store method"""
        DB().store_dp_requests(models = models)

    def run_action(self, iter_count = 0, _max = 0) -> None:
        """run action"""
        try:
            task_queue = Queue()
            done_queue = Queue()
            jobs = []
            for i in range(PROCESS_COUNT):
                process = Process(target=InProcess(contract=self.etnyContract, w3=self._w3).run, args=(task_queue, done_queue, _max))
                jobs.append(process)
                process.start()

            _iter = 0
            for i in iter_count:
                task_queue.put(i)

                _iter += 1
                if _iter and _iter % PROCESS_COUNT == 0:
                    _loop = PROCESS_COUNT * PROCESS_COUNT
                    _iter = 0
                    for _ in range(_loop):
                        try:
                            result = done_queue.get(timeout=7)
                            GetDPRequests.results.append(result)
                        except Exception as err: # pylint: disable=broad-except
                            print('error = ', i, err, type(err))
                            if '_queue.Empty' in str(type(err)):
                                break
                            continue

                    if len(GetDPRequests.results) >= PROCESS_COUNT:
                        GetDPRequests.store(models = GetDPRequests.results)
                        GetDPRequests.results = []

            for i in GetDPRequests.results:
                GetDPRequests.store(models = GetDPRequests.results)
                GetDPRequests.results = []

            print('after loop')
            task_queue.put('STOP')
            task_queue.close()
            done_queue.close()
            for i in jobs:
                i.kill()
        
        except Exception as err: # pylint: disable=broad-except
            print('global error', err)

    def run(self, total = 0, start_point = 0):
        super().run()
        _total = total if total else self.etnyContract.functions._getDPRequestsCount().call() # pylint: disable=protected-access
        _max = _total
        iter_count = range(start_point, _max + 1, PROCESS_COUNT)
        self.run_action(iter_count=iter_count, _max = _max)

    def get_missing_records_inline(self):
        """getMissingRecordsInline"""
        pass

    def get_missing_records(self, last_page = 1, per_page = 30):
        """getMissingRecords"""
        try:
            count, current_iter, _max, items = map(lambda x: x if ',' in x else int(x), DB().get_missing_records(last_page=last_page, per_page=per_page).split('-'))    
        except ValueError:
            print('finishd...')
            return

        items = filter(lambda x: x, items.split(','))
        print(f'''
            count = {count} - {type(count)}, 
            current_iter = {current_iter} - {type(current_iter)}, 
            _max = {_max} - {type(_max)}, 
            items = {items} - {type(items)}
        ''')
        print([item for item in items])
        for _ in range(count):
            pass
        # return self.get_missing_records(last_page=current_iter)

if __name__ == '__main__':
    GetDPRequests()