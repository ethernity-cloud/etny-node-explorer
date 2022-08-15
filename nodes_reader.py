#!/usr/bin/python3

from urllib import request
import web3, argparse, sys, os, asyncio, json, csv, time
from packaging import version
from web3 import Web3
from web3.middleware import geth_poa_middleware
from node import Node
from multiprocessing import Process, cpu_count
from helpers.exceptions import NotFoundException, DatabaseEngineNotFoundError
import helpers.config as config
from requests.exceptions import ConnectionError

try:
    if config.config['DATABASE']['engine'] != 'MYSQL':
        raise DatabaseEngineNotFoundError('For DB Engine is used Sqlite')
    from helpers.mysql_database import MysqlDatabase as Database, dbException
except (ImportError, DatabaseEngineNotFoundError) as e:
    print(e)
    from helpers.sqlite_database import SqliteDatabase as Database, dbException

# config section

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
        
        if self.is_child:
            self._childProcess()
        else:

            # Database().dropTable()
            # init database
            Database().init()

            # init database

            self._parentProcess(is_inline_process=True)
            #self._parentProcess()

        # self._action()


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

    def _childProcess(self, block_identifier = None) -> None:
        if block_identifier:
            self.block_identifier = block_identifier
        print('----------block identifier = ', self.block_identifier)
        fork_process(block_identifier = self.block_identifier)

    def _async_run(self, i):
        asyncio.run(self.action(cmd = f'python3 nodes_reader.py -c True -b {i}'))

    def _parentProcess(self, is_inline_process = True):
        [
            currentBlock,
            startBlockNumber
        ] = self._action_args()

        threads = []
        _iter = 0
        print(startBlockNumber, currentBlock, config.BASE_LOOP_ITER)
        for i in range(startBlockNumber, currentBlock, config.BASE_LOOP_ITER):
            methodName = self._async_run if not is_inline_process else self._childProcess
            print('len = ', len(threads))
            t = Process(target = methodName, args = (i, ))
            t.daemon = True
            t.start()
            threads.append(t)
            if len(threads) > int(cpu_count() * 5):
                print('*', cpu_count(), i, len(threads))
                for thread in threads:
                    thread.join()
                threads = []
            _iter += 1
            if _iter > 300:break
        print('iter = ', _iter)

    async def action(self, cmd = ''):
        inlineProc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        stdout, stderr = await inlineProc.communicate()
        print(cmd, ' -> ',stdout.decode())
        if stderr:
            print(stderr.decode())

    def _action(self):
        [
            currentBlock,
            startBlockNumber,
        ] = self._action_args()

        etnyContract = self._get_etnyContract()
        
        previous_counter = None
        for order_id in range(startBlockNumber, currentBlock, 10):
            currentCounter = etnyContract.functions._getDPRequestsCount().call(block_identifier=i)
            if currentCounter != previous_counter:
                if_exists = Database().select_one(single = 'id, order_id', id = currentCounter)
                [print('*-*-*' * 10) for x in range(5)]
                print(if_exists)
                [print('*-*-*' * 10) for x in range(5)]
                if if_exists and if_exists[1] > order_id:
                    print('is updated------------')
                    Database().update(fields = {'order_id': order_id}, where = {'id': currentCounter}).commit()
                else:
                    previous_counter = currentCounter
                    Database().insert(_id = currentCounter, order_id=order_id)
                    if currentCounter % 10 == 0:
                        Database().commit()
            print('reading block: ', order_id, currentCounter)
            if i > startBlockNumber + 1000:break

        Database().commit()

        nodes = self.__read_csv_file(self._nodesFile)

        startingCount = 0
        if len(nodes.keys()) > 0:
            startingCount = etnyContract.functions._getDPRequestsCount().call(block_identifier=startBlockNumber)

        endingCount = etnyContract.functions._getDPRequestsCount().call()

        node_index = len(nodes.keys()) + 1
        for i in range(startingCount, endingCount):
            request = etnyContract.functions._getDPRequest(i).call()
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
                print("Connected...")
                print('block number', blockNumber)
                print('timestamp', timestamp)
                print('current block number', currentBlock)

            startBlockNumber = blockNumber + 10
            max_node = Database().select_one(single = 'max(id) as id, order_id')
            if max_node:
                if not self.is_child:
                    print('max node = ', max_node)
                    
                startBlockNumber = max_node[1]

            return [
                currentBlock,
                startBlockNumber
            ]
        except (dbException, TypeError) as e:
            print('-----', e)
            time.sleep(0.01)
            return self._action_args()

    def __read_contract_abi(self) -> str:
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/entyContract.abi') as r:
                return r.read()
        except Exception as e:
            return None

    def __read_index_content(self) -> dict:
        if os.path.exists(self._indexFile):
            with open(self._indexFile) as r:
                return json.load(r)
        return {}

    def __write_index_content(self, jsonContent) -> dict:
        with open(self._indexFile, "w") as w:
            w.write(json.dumps(jsonContent))

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
            print(e)
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


class fork_process(Reader):
    previous_counters = set()
    etnyContract = None
    def __init__(self, block_identifier = None) -> None:
        self.block_identifier = int(block_identifier)

        self.is_child = False
        self._baseConfig()
        self.etnyContract = self._get_etnyContract()

        self.init()

    def init(self):

        itr = 0
        commit_limit = 100
        for order_id in range(self.block_identifier, self.block_identifier + config.BASE_LOOP_ITER, int(config.BASE_LOOP_ITER / 100)):
            currentCounter = self.insert(order_id=order_id)
            itr += 1
            if itr >= commit_limit:
                Database().commit()
                itr = 0
        print('debug: ', itr, currentCounter,  order_id, self.block_identifier)

        if itr and itr < commit_limit:
            Database().commit()


    def insert(self, order_id, recursive_count = 0):
        try:
            currentCounter = self.etnyContract.functions._getDPRequestsCount().call(block_identifier=order_id)
            try:
                if currentCounter not in self.previous_counters:
                    if len(self.previous_counters) > 10:
                        self.previous_counters = set()
                    self.previous_counters.add(currentCounter)
                    if_exists = Database().select_one(single = 'id, order_id', id = currentCounter)
                    print(if_exists, order_id)
                    if not if_exists:
                        Database().insert(_id = currentCounter, order_id=order_id)
                    elif if_exists and if_exists[1] > order_id:
                        print('is updated------------')
                        Database().update(fields = {'order_id': order_id}, where = {'id': currentCounter}).commit()
                    
            except dbException as e:
                [print('--*' * 1) for x in range(10)]
                print(e)
                [print('**-' * 1) for x in range(10)]
                time.sleep(.01)
                self.insert(order_id=order_id)
            return currentCounter
        except ConnectionError as e:
            print('*|* - ', order_id, e)
            if recursive_count and recursive_count % 10 == 0:
                time.sleep(0.01)
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