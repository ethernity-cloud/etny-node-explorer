#!/usr/bin/python3

import multiprocessing
from platform import node
from urllib import request
import web3, argparse, sys, os, asyncio, json, csv, time
from packaging import version
from web3 import Web3
from web3.middleware import geth_poa_middleware
from node import Node
from multiprocessing import Process, cpu_count, Manager
from helpers.exceptions import NotFoundException, DatabaseEngineNotFoundError, BreackFromLoopException
import helpers.config as config    
from helpers.terminated_task import TerminatedTask

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



class sharedObject(object):
    def __init__(self, initval = [], proxyID = 0):
        manager = Manager()
        self.val = manager.list()
        self.lock = multiprocessing.Lock()

    def append(self, value):
        with self.lock:
            if len(self.val) > LIMIT_OF_THREADS:
                self.val = []
            if value not in self.val:
                self.val.append(value)
    @property
    def value(self):
        with self.lock:
            return self.val


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

        try:
            if self.is_child:
                self._childProcess()
            else:

                # Database().dropTable()
                Database().init()

                # n = Node(
                #     id = 1,
                #     order_id = 2,
                #     address = '0x02B143Fe76f4F8C4A2E792311664d24759c49d52', 
                #     cpu = 1, 
                #     memory = 1, 
                #     storage = 40, 
                #     bandwith = 1, 
                #     duration = 60, 
                #     status = 0, 
                #     cost = 2
                # )

                # print(n.public())
                # print(n.private())

                # Database().insert(node = n)
                # Database().update(node = n)
                # Database().commit()
                # sys.exit()

                # init database

                # [self._log(f"{str(getattr(config.bcolors, x)).split('.')[1]} - something", str(getattr(config.bcolors, x)).split('.')[1]) for x in dir(config.bcolors) if not x.startswith('__')]

                asyncio.run(self._parentProcess(is_inline_process=True))
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

    def _childProcess(self, block_identifier = None, shared_object = None) -> None:
        if block_identifier:
            self.block_identifier = block_identifier
        self._log(f'----------block identifier = {self.block_identifier}', 'message')
        fork_process(block_identifier = self.block_identifier, shared_object=shared_object)

    def _async_run(self, i, chared_object = None):
        cmd = f'python3 nodes_reader.py -c True -b {i}'
        # asyncio.run(self.action(cmd = f'python3 nodes_reader.py -c True -b {i}'))
        t = TerminatedTask(cmd = cmd, time_limit=TASK_LIFE_TIME)
        result = t.run()
        print('\n-----')
        print((result['stdout'] if result['stdout'] else result['stderr']))

    def joinSingle(self):
        while len(multiprocessing.active_children()) > LIMIT_OF_THREADS - 1:
            pass
        print("join single child; left childrend count = {0}".format(len(multiprocessing.active_children())))

    def joinAll(self):
        for p in multiprocessing.active_children():
            p.join()
        print("join all child; left childrend count = {0}".format(len(multiprocessing.active_children())))

    async def _parentProcess(self, is_inline_process = True):
        [
            startBlockNumber,
            currentBlock
        ] = self._action_args()

        _iter = 0
        self._log(f"{startBlockNumber} {currentBlock} {config.BASE_LOOP_ITER}", 'info')

        shared_object = sharedObject(initval=[])

        for i in range(startBlockNumber, currentBlock, config.BASE_LOOP_ITER):
            active_childrens_count = len(multiprocessing.active_children())
            if active_childrens_count > LIMIT_OF_THREADS:
                print('----------wait for threads: ', active_childrens_count)
                time.sleep(.5)
                continue

            methodName = self._async_run if not is_inline_process else self._childProcess
            self._log(f'len =  {active_childrens_count}', 'info')
            thread = Process(target = methodName, args = (i, shared_object))
            # thread.daemon = True
            thread.start()

            # terminate on demand
            if is_inline_process:
                self._log(f'---progress: {thread.pid}', 'info')
                asyncio.create_task(self.until_finished(thread, i))
            # terminate on demand

            _iter += 1
            # if _iter > 300:break
        self._log(f'iter =  {_iter}')

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

    def _action(self):
        
        nodes = self.__read_csv_file(self._nodesFile)

        startingCount = 0
        if len(nodes.keys()) > 0:
            startingCount = self.etnyContract.functions._getDPRequestsCount().call(block_identifier=startBlockNumber)

        endingCount = self.etnyContract.functions._getDPRequestsCount().call()

        node_index = len(nodes.keys()) + 1
        for i in range(startingCount, endingCount):
            request = self.etnyContract.functions._getDPRequest(i).call()
            print("reading request ", i)
            if request[0] not in nodes:
                node = Node(node_index, request[0], request[1], request[2], request[3], request[4], request[5], request[6],
                            request[7],
                            self.__get_timestamp_from_request(i), self.__get_timestamp_from_request(i))
                nodes[request[0]] = node
                node_index = node_index + 1
            else:
                nodes[request[0]].last_updated = self.__get_timestamp_from_request(i)

        if len(nodes) > 0:
            with open(self._nodesFile, 'w',newline='') as output_file:
                writer = csv.writer(output_file, dialect="excel-tab")
                for k, row in nodes.items():
                    writer.writerow([row.no, row.address, row.cpu, row.memory, row.storage, row.bandwith, row.duration, row.status, row.cost, row.created_on, row.last_updated])

    def _get_etnyContract(self):
        return self._w3.eth.contract(address=self._contract, abi=self.__read_contract_abi())

    def _action_args(self):
        try:
            firstContractTx = "0x90eeb0a0680034c8c340dfa60b773ed77b060d6a966596059610981486d312f4"

            blockNumber = self._w3.eth.getTransaction(firstContractTx).blockNumber
            timestamp = self._w3.eth.getBlock(blockNumber).timestamp
            currentBlock = self._w3.eth.blockNumber

            if not self.is_child:
                self._log("Connected...")
                self._log(f'block number {blockNumber}', 'info')
                self._log(f'timestamp {timestamp}', 'info')
                self._log(f'current block number {currentBlock}', 'info')

            startBlockNumber = blockNumber + 10
            max_node = Database().select_one(single = 'max(id) as id, order_id')
            if max_node:
                if not self.is_child:
                    self._log(f'max node = {max_node}', 'info')
                    
                startBlockNumber = max_node[1]

            return [
                startBlockNumber,
                currentBlock
            ]
        except (dbException, TypeError) as e:
            self._log(f'-----{e}', 'error')
            time.sleep(0.01)
            return self._action_args()

    def __read_contract_abi(self) -> str:
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/entyContract.abi') as r:
                return r.read()
        except Exception as e:
            return None

    def __read_csv_file(self, file) -> None:
        rows = {}
        try:
            if not os.path.exists(file):
                raise NotFoundException

            with open(file) as fileContent:
                for line in csv.reader(fileContent, dialect="excel-tab"):
                    _row = Node(line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7], line[8], line[9], line[10])
                    rows[_row.address] = _row
        except Exception as e:
            self._log(e, 'error')
        finally:
            return rows

    def __get_timestamp_from_request(self, request_id):
        # while str(request_id) not in values.keys():
        while Database().select_one(singe = 'id', id = request_id):
            request_id = request_id - 1

        # block_number = values[str(request_id)]
        block_number = Database().select_one(single = 'order_id', id = request_id)
        time_stamp = self._w3.eth.getBlock(block_number).timestamp

        return time_stamp

    def _log(self, message = '', mode = '_end', hide_prefix = True, terminate = False) -> None:
        mode = str(mode.upper() if type(mode) == str else config.bcolors[mode].name)
        prefix = f"{config.bcolors[mode].value}{config.bcolors.BOLD.value}{config.bcolors[mode].name}{config.bcolors._END.value}: " if mode not in ['_END', 'BOLD', 'UNDERLINE'] and not hide_prefix else ""
        print(f"{prefix}{config.bcolors[mode].value}{str(message)}{config.bcolors._END.value}")
        if terminate: sys.exit()

class fork_process(Reader):
    previous_counters = set()
    etnyContract = None
    shared_object = None
    def __init__(self, block_identifier = None, shared_object = None) -> None:
        try:
            self.block_identifier = int(block_identifier)
            self.shared_object = shared_object
            self.is_child = False
            self._baseConfig()
            self.etnyContract = self._get_etnyContract()

            self.init()
        except KeyboardInterrupt as e:
            pass

    def init(self):

        itr = 0
        commit_limit = 100
        for order_id in range(self.block_identifier, self.block_identifier + config.BASE_LOOP_ITER, int(config.BASE_LOOP_ITER / 100)):
            currentCounter = self.insert(order_id=order_id)
            itr += 1
            if itr >= commit_limit:
                Database().commit()
                itr = 0
        self._log(f'debug: {itr}, {currentCounter},  {order_id}, {self.block_identifier}', 'message')

        if itr and itr < commit_limit:
            Database().commit()


    def insert(self, order_id, recursive_count = 0):
        try:
            currentCounter = self.etnyContract.functions._getDPRequestsCount().call(block_identifier=order_id)
            try:
                insert_id = currentCounter if currentCounter > 0 else -1

                # inline buffer
                if insert_id in self.previous_counters:return
                if len(self.previous_counters) > 20:
                    self.previous_counters = set()
                self.previous_counters.add(insert_id)

                # shared buffer
                if self.shared_object:
                    if int(currentCounter) in self.shared_object.value and not recursive_count:return
                    self.shared_object.append(currentCounter)
                    print('shared object = ', currentCounter, self.shared_object.value, recursive_count, os.getpid())

                if_exists = Database().select_one(single = 'id, order_id', id = insert_id)
                if not if_exists or (if_exists and if_exists[1] > order_id):

                    request = self.etnyContract.functions._getDPRequest(currentCounter).call()
                    node = Node(
                        id = insert_id,
                        order_id = order_id
                    )
                    items = ['address', 'cpu', 'memory', 'storage', 'bandwith', 'duration', 'status', 'cost']
                    for key, item in enumerate(items):
                        try:
                            setattr(node, item, request[key])
                        except IndexError as e:
                            pass
                        
                    if not if_exists:
                        Database().insert(node)
                        print('after inserting: ', node.instance())

                    elif if_exists and if_exists[1] > order_id:
                        self._log(f'is updated------------ {str(node.instance())}', 'message')
                        Database().update(node).commit()
                    
            except dbException as e:
                [self._log('--*' * 1, 'error') for x in range(10)]
                time.sleep(.01)
                self.insert(order_id=order_id)
            return insert_id
        except ConnectionError as e:
            self._log(f'*|* - {order_id}, {e} {recursive_count}', 'warning')
            if recursive_count and recursive_count % 10 == 0:
                time.sleep(0.1)
            self._baseConfig()
            self.etnyContract = self._get_etnyContract()
            return self.insert(order_id = order_id, recursive_count=recursive_count + 1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ethernity PoX request")
    parser.add_argument("-c", "--is_child", default=False)
    parser.add_argument("-b", "--block_identifier", default=0)
    parser = parser.parse_args()
    
    Reader(
        is_child=parser.is_child, 
        block_identifier=parser.block_identifier
    )