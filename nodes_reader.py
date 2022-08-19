#!/usr/bin/python3

import multiprocessing
from pickle import FALSE
from platform import node
import web3, argparse, sys, os, asyncio, json, csv, time
from packaging import version
from web3 import Web3
from web3.middleware import geth_poa_middleware
from node import Node
from multiprocessing import Process, cpu_count, Manager
from helpers.exceptions import NotFoundException, DatabaseEngineNotFoundError, BreackFromLoopException
import helpers.config as config
from helpers.terminated_task import TerminatedTask
from typing import Union
import gc

from requests.exceptions import ConnectionError

try:
    if config.config['DATABASE']['engine'] != 'MYSQL':
        raise DatabaseEngineNotFoundError('For DB Engine is used Sqlite')
    from helpers.mysql_database import MysqlDatabase as Database, dbException
except (ImportError, DatabaseEngineNotFoundError) as e:
    from helpers.sqlite_database import SqliteDatabase as Database, dbException

# config section

TASK_LIFE_TIME = 60
LIMIT_OF_THREADS = int(cpu_count() * 5)
LOG_IS_ENABLED = False
FREE_MEMORY_IN_INTERVAL = False


class sharedObject(object):
    def __init__(self):
        manager = Manager()
        self.val = manager.list()
        self.lock = multiprocessing.Lock()

    def append(self, value):
        with self.lock:
            if len(self.val) > LIMIT_OF_THREADS:
                self.val = []
            if value not in self.val:
                self.val.append(value)
    
    def reset(self):
        with self.lock:
            self.val = []

    @property
    def value(self):
        with self.lock:
            return self.val

GLOBAL_LOCK = multiprocessing.Lock()

class Reader:

    _w3 = None
    _contract = None
    _indexFile = None
    _nodesFile = None
    _httpProvider = None

    def __init__(self, is_child = False, block_identifier = None) -> None:
        self.is_child = is_child
        self.block_identifier = block_identifier
        self._baseConfig()
        self.is_inline_process = True
        
        try:
            if self.is_child:
                self._childProcess()
            else:

                # Database().dropTable()

                # init database
                Database().init()

                ''''''
                ''''''

                # [self._log(f"{str(getattr(config.bcolors, x)).split('.')[1]} - something", str(getattr(config.bcolors, x)).split('.')[1]) for x in dir(config.bcolors) if not x.startswith('__')]

                #self._parentProcess()
                asyncio.run(self._parentProcess())
        except KeyboardInterrupt as e:
            for process in multiprocessing.active_children():
                process.terminate()  
            self._log('bye...', 'MESSAGE')

    def _baseConfig(self) -> None:
        self._httpProvider = config.config['DEFAULT']['HttpProvider']
        self._contract = config.config['DEFAULT']['ContractAddress']
        self._indexFile = config.config['DEFAULT']['IndexFile']
        self._nodesFile = config.config['DEFAULT']['CSVFile']

        self._w3 = Web3(Web3.HTTPProvider(self._httpProvider))
        if version.parse(web3.__version__) < version.parse('5.0.0'):
            self._w3.middleware_stack.inject(geth_poa_middleware, layer=0)
        else:
            self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    def _childProcess(self, block_identifier = None, shared_object = None, next_block_identifier = None) -> None:
        if block_identifier:
            self.block_identifier = block_identifier
        self._log(f'----------block identifier = {self.block_identifier}', 'message', log_mode=LOG_IS_ENABLED)
        fork_process(block_identifier = self.block_identifier, shared_object=shared_object, next_block_identifier = next_block_identifier)

    def _async_run(self, i, chared_object = None):
        cmd = f'python3 nodes_reader.py -c True -b {i}'
        # asyncio.run(self.action(cmd = f'python3 nodes_reader.py -c True -b {i}'))
        t = TerminatedTask(cmd = cmd, time_limit=TASK_LIFE_TIME)
        result = t.run()
        print('\n-----')
        print((result['stdout'] if result['stdout'] else result['stderr']))

    def joinAll(self):
        for p in multiprocessing.active_children():
            p.join()
        print("waiting for every process to be finishd...".format(len(multiprocessing.active_children())))

    def _loopContent(self, block_identifier, shared_object, _iter, next_block_identifier = None):
        active_childrens_count = len(multiprocessing.active_children())
        if active_childrens_count > LIMIT_OF_THREADS - 1:
            self._log(f'removing the process from the stack {active_childrens_count}', 'error')
            time.sleep(.5)
            return self._loopContent(block_identifier, shared_object, _iter, next_block_identifier = next_block_identifier)

        methodName = self._async_run if not self.is_inline_process else self._childProcess
        self._log(f'len =  {active_childrens_count}, iter = {_iter}', 'info')
        thread = Process(target = methodName, args = (block_identifier, shared_object, next_block_identifier))
        thread.daemon = True
        thread.start()

        # terminate on demand
        if self.is_inline_process:
            pass # asyncio.create_task(self.until_finished(thread, i))
        # terminate on demand

        if FREE_MEMORY_IN_INTERVAL:
            if _iter and _iter % int(config.BASE_LOOP_ITER / 2) == 0:
                self._log('need to join threads...')
                if self.is_inline_process:
                    shared_object.reset()
                    time.sleep(1)
                self.joinAll()
                print(gc.get_count())
                gc.collect()
                time.sleep(1)   

    def generatorWrapper(self, callback = None):
        _iter = 1
        while True:
            try:
                blocks = self._getMissingRecords(limit=_iter)
                _iter += 1
                inline_counter = 0
                for block in blocks:
                    callback(block)
                    inline_counter += 1
                if not inline_counter:break
            except Exception as e:
                print(e)
                break
        print('len = ', _iter)

    async def _parentProcess(self):
        [
            startBlockNumber,
            currentBlock
        ] = self._action_args()

        old_startBlockNumber = startBlockNumber
        _iter = 0
        self._log(f"{startBlockNumber} {currentBlock} {config.BASE_LOOP_ITER}", 'info')
        shared_object = sharedObject()

        # main loop, starts from latest transaction
        # for block_identifier in range(startBlockNumber, currentBlock, config.BASE_LOOP_ITER):
        #     self._loopContent(block_identifier=block_identifier, shared_object=shared_object, _iter = _iter)             
        #     _iter += 1

        self._log(f'-----------iter =  {_iter} {len(multiprocessing.active_children())}')

        shared_object.reset()
        self.joinAll()
        self._log('------Searching for missing items, Please wait...', 'error')


        # checking for missing records
        _iter = 0
        def wrapper(block):
            [current_id, _block_identifier, next_block_identifier] = block
            self._loopContent(block_identifier=_block_identifier, shared_object=shared_object, _iter = _iter, next_block_identifier = next_block_identifier)
        
        self.generatorWrapper(callback = wrapper)

        self._log(f'----------finished all the threads')

        sys.exit()

    def _getMissingRecords(self, limit = 1):
        per_request = 10
        query = f'''select 
                        (d.id + 1) as id, 
                        block_identifier,
                        (select min(block_identifier) from orders where block_identifier > d.block_identifier) as next_block_identifier
                    from orders d where id > -1 and not exists (select id from orders where id = d.id + 1)
                    and d.id < (select max(id) from orders) and d.id < 300
                    limit {limit * per_request if limit > 1 else 0}, {per_request}
                '''
        result = Database().raw_select(query=query)
        if LOG_IS_ENABLED:
            for item in result:
                [_id, block_identifier, next_block_identifier] = item
                print(f'id = {_id}, block_identifier = {block_identifier} next_block_identifier = {next_block_identifier}')
        return result

    async def action(self, cmd = ''):
        inlineProc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        stdout, stderr = await inlineProc.communicate()
        print(cmd, ' -> ',stdout.decode())
        if stderr:
            print(stderr.decode())

    async def until_finished(self, thread, i) -> None:
        t = time.time()
        while True:
            try:
                if not thread.is_alive():
                    raise BreackFromLoopException('force')
                if int(time.time() - t) >= TASK_LIFE_TIME:
                    self._log(f'-----truncate task force: {thread.pid}', 'warning')
                    thread.terminate()
                    raise BreackFromLoopException()
            except BreackFromLoopException as e:
                break
            await asyncio.sleep(1)

    def _get_etnyContract(self):
        return self._w3.eth.contract(address=self._contract, abi=self._read_contract_abi())

    def _action_args(self):
        try:
            firstContractTx = "0x90eeb0a0680034c8c340dfa60b773ed77b060d6a966596059610981486d312f4"

            firstBlockNumber = self._w3.eth.getTransaction(firstContractTx).blockNumber
            timestamp = self._w3.eth.getBlock(firstBlockNumber).timestamp
            currentBlock = self._w3.eth.blockNumber

            if not self.is_child:
                self._log("Connected...")
                self._log(f'block number {firstBlockNumber}', 'info')
                self._log(f'timestamp {timestamp}', 'info')
                self._log(f'current block number {currentBlock}', 'info')

            startBlockNumber = firstBlockNumber + 10
            max_node = Database().select_one(single = 'id, max(block_identifier) as block_identifier')

            print(max_node)

            if max_node:
                if not self.is_child:
                    self._log(f'max node = {max_node}', 'info')
                    
                startBlockNumber = max_node[1]

            return [
                # firstBlockNumber + 10,
                startBlockNumber,
                currentBlock
            ]
        except (dbException, TypeError) as e:
            self._log(f'-----{e}', 'error')
            time.sleep(0.01)
            return self._action_args()

    def _read_contract_abi(self) -> str:
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/entyContract.abi') as r:
                return r.read()
        except Exception as e:
            return None

    def _log(self, message = '', mode = '_end', hide_prefix = True, terminate = False, log_mode = True) -> None:
        if not log_mode:return
        mode = str(mode.upper() if type(mode) == str else config.bcolors[mode].name)
        prefix = f"{config.bcolors[mode].value}{config.bcolors.BOLD.value}{config.bcolors[mode].name}{config.bcolors._END.value}: " if mode not in ['_END', 'BOLD', 'UNDERLINE'] and not hide_prefix else ""
        print(f"{prefix}{config.bcolors[mode].value}{str(message)}{config.bcolors._END.value}")
        if terminate: sys.exit()

class fork_process(Reader):
    local_buffer = set()
    etnyContract = None
    shared_object = None
    next_block_identifier = None
    def __init__(self, block_identifier = None, shared_object = None, next_block_identifier = None) -> None:
        try:
            self.block_identifier = int(block_identifier)
            self.shared_object = shared_object
            self.is_child = False
            self.next_block_identifier = next_block_identifier
            self._baseConfig()
            self.etnyContract = self._get_etnyContract()

            print('----------before')
            etnyContract = self._w3.eth.contract(address=self._contract, abi=self._read_contract_abi())
            for item in [12867544, 12867545, 12867546, 12867547, 12867548, 12867549, 12867550, 12867551, 12867552]:
                result = self.etnyContract.functions._getDPRequestsCount().call(block_identifier=item)
                print(result)
            print('----------after')
            sys.exit()



            print('----------before')
            for item in [12867544, 12867545, 12867546, 12867547, 12867548, 12867549, 12867550, 12867551, 12867552]:
                result = self.etnyContract.functions._getDPRequestsCount().call(block_identifier=item)
                print(result)
            print('----------after')

            sys.exit()

            if self.next_block_identifier != None:
                self.get_missing_items()
            else:
                self.get_all_items()
        except KeyboardInterrupt as e:
            pass

    def get_all_items(self):
        itr = 0
        for block_identifier in range(self.block_identifier, self.block_identifier + config.BASE_LOOP_ITER, int(config.BASE_LOOP_ITER / 100)):
            self.insert(block_identifier=block_identifier)
            itr += 1
        self._log(f'debug: {itr}, {block_identifier}, {self.block_identifier}', 'message')

    # for missing items
    def get_missing_items(self):
        itr = 0

        for block_identifier in range(self.block_identifier + 1, self.next_block_identifier):
            print(
                block_identifier
            )
            self.insert(block_identifier=block_identifier)
            itr += 1
        self._log(f'debug for missing items: {itr}, {self.block_identifier} {self.next_block_identifier}', 'message')

    def insert(self, currentCounter = None, block_identifier = None, recursive_count = 0):
        try:
            currentCounter = self.etnyContract.functions._getDPRequestsCount().call(block_identifier=block_identifier)
            try:
                insert_id = currentCounter if currentCounter > 0 else -1

                # inline buffer
                if insert_id in self.local_buffer:return
                if len(self.local_buffer) > 20:
                    self.local_buffer = set()
                self.local_buffer.add(insert_id)


                # shared buffer
                if self.shared_object:
                    try:
                        if int(insert_id) in self.shared_object.value and not recursive_count:return
                        self.shared_object.append(insert_id)
                        # print('shared object = ', currentCounter, self.shared_object.value, recursive_count, os.getpid())
                    except ConnectionRefusedError as c:
                        print('----------connection refused...', str(c))

                if_exists = Database().select_one(single = 'id, block_identifier', id = insert_id)
                if not if_exists or (if_exists and if_exists[1] > block_identifier):
                    node = self._getNode(currentCounter, insert_id, block_identifier)
                    if not node:return
                    # with GLOBAL_LOCK:
                    Database().reConnect(config=config.config)
                    if not if_exists:
                        node.created_on = self._getTimestamp(block_identifier=block_identifier)
                        Database().insert(node)

                    elif if_exists and if_exists[1] > block_identifier:
                        self._log(f'is updated------------ {str(node.instance())}', 'message', log_mode=LOG_IS_ENABLED)
                        Database().update(node).commit()
                    
            except dbException as e:
                [self._log('--*' * 1, 'error') for x in range(10)]
                time.sleep(.01)
                return self.insert(currentCounter = currentCounter, block_identifier=block_identifier)
            return insert_id
        except (ConnectionError, Exception) as e:
            if type(e) == ValueError and '--pruning=archive' in str(e):
                print(e)
                return
            self._log(f'*|* - {block_identifier}, {e} {recursive_count} {os.getpid()} {type(e)}', 'warning')
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            if recursive_count and recursive_count % 10 == 0:
                time.sleep(0.1)
            self._baseConfig()
            self.etnyContract = self._get_etnyContract()
            return self.insert(currentCounter = currentCounter, block_identifier = block_identifier, recursive_count=recursive_count + 1)

    def _getNode(self, currentCounter, insert_id, block_identifier) -> Node | None:
        request = self.etnyContract.functions._getDPRequest(currentCounter).call()
        if not request:
            self._log("there no request at all ------", "error")
            return None
                
        node = Node(
            id = insert_id,
            block_identifier = block_identifier
        )

        items = ['address', 'cpu', 'memory', 'storage', 'bandwith', 'duration', 'status', 'cost']
        for key, item in enumerate(items):
            try:
                setattr(node, item, request[key])
            except IndexError as e:
                pass
        return node

    def _getTimestamp(self, block_identifier, recursived_count = 0) -> int:
        try:
            timestamp = self._w3.eth.getBlock(block_identifier).timestamp
            if not timestamp and recursived_count < 10:
                return self._getTimestamp(block_identifier=block_identifier - 1, recursived_count=recursived_count + 1)
            return timestamp
        except Exception as e:
            self._log('error while getting timestamp...')
        return int(time.time())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ethernity PoX request")
    parser.add_argument("-c", "--is_child", default=False)
    parser.add_argument("-b", "--block_identifier", default=0)
    parser = parser.parse_args()
    
    Reader(
        is_child=parser.is_child, 
        block_identifier=parser.block_identifier
    )