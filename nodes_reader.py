#!/usr/bin/python3

from ast import parse
import web3, configparser, argparse, os, asyncio, json, csv, time
from packaging import version
from web3 import Web3
from web3.middleware import geth_poa_middleware
from node import Node
from multiprocessing import Process, cpu_count
from helpers.exceptions import NotFoundException


try:
    from helpers.mysql_database import MysqlDatabase as Database, dbException
    #import non_existing_module_to_trigger_import_error
except ImportError as e:
    from helpers.sqlite_database import SqliteDatabase as Database, dbException


# config section

BASE_LOOP_ITER = 1000 

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

            self._parentProcess()

        # self._action()


    def _baseConfig(self) -> None:
        config = configparser.ConfigParser()
        config.read('config.env')
        self._httpProvider = config['DEFAULT']['HttpProvider']

        self._contract = config['DEFAULT']['ContractAddress']
        self._indexFile = config['DEFAULT']['IndexFile']
        self._nodesFile = config['DEFAULT']['CSVFile']

        self._w3 = Web3(Web3.HTTPProvider(self._httpProvider))
        if version.parse(web3.__version__) < version.parse('5.0.0'):
            self._w3.middleware_stack.inject(geth_poa_middleware, layer=0)
        else:
            self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    def _childProcess(self) -> None:
        print('----------block identifier = ', self.block_identifier)
        fork_process(block_identifier = self.block_identifier)

    def _async_run(self, i):
        asyncio.run(self.action(cmd = f'python3 nodes_reader.py -c True -b {i}'))

    def _parentProcess(self):
        [
            etnyContract,
            currentBlock,
            startBlockNumber,
            values
        ] = self._action_args()


        threads = []
        for i in range(startBlockNumber, currentBlock, BASE_LOOP_ITER):
            t = Process(target = self._async_run, args = (i, ))
            t.start()
            threads.append(t)
            if len(threads) > int(cpu_count() * 3):
                for thread in threads:
                    thread.join()
                threads = []

            print('---------------', i, len(threads))

            if i > startBlockNumber + int(BASE_LOOP_ITER * 10):break


    async def action(self, cmd = ''):
        inlineProc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        stdout, stderr = await inlineProc.communicate()
        print(cmd, ' -> ',stdout.decode())
        if stderr:
            print(stderr.decode())

    def _action(self):
        [
            etnyContract,
            currentBlock,
            startBlockNumber,
            values
        ] = self._action_args()

        for i in range(startBlockNumber, currentBlock, 10):
            currentCounter = etnyContract.functions._getDPRequestsCount().call(block_identifier=i)
            if currentCounter not in values:
                print('not in d -----')
                values[currentCounter] = i
                if currentCounter % 10 == 0:
                    self.__write_index_content(values)
            print('reading block: ', i, currentCounter)
            if i > startBlockNumber + 1000:break

        # write json back
        self.__write_index_content(values)

        # get json again
        values = self.__read_index_content()

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
                            self.__get_timestamp_from_request(values, i), self.__get_timestamp_from_request(values, i))
                nodes[request[0]] = node
                node_index = node_index + 1
            else:
                nodes[request[0]].last_updated = self.__get_timestamp_from_request(values, i)

        if len(nodes) > 0:
            with open(self._nodesFile, 'w',newline='') as output_file:
                writer = csv.writer(output_file, dialect="excel-tab")
                for k, row in nodes.items():
                    writer.writerow([row.no, row.address, row.cpu, row.memory, row.storage, row.bandwith, row.duration, row.status, row.cost, row.created_on, row.last_updated])

    def _action_args(self):
        etnyContract = self._w3.eth.contract(address=self._contract, abi=self.__read_contract_abi())
        firstContractTx = "0x90eeb0a0680034c8c340dfa60b773ed77b060d6a966596059610981486d312f4"

        blockNumber = self._w3.eth.getTransaction(firstContractTx).blockNumber
        timestamp = self._w3.eth.getBlock(blockNumber).timestamp
        currentBlock = self._w3.eth.blockNumber

        if not self.is_child:
            print("Connected...")
            print('block number', blockNumber)
            print('timestamp', timestamp)
            print('current block number', currentBlock)

        values = self.__read_index_content()
        startBlockNumber = blockNumber + 10
        if len(values.keys()) > 0:
            startBlockNumber = values[max(values, key=values.get)]

        return [
            etnyContract,
            currentBlock,
            startBlockNumber,
            values
        ]

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

    def __get_timestamp_from_request(self, values, request_id):
        while str(request_id) not in values.keys():
            request_id = request_id - 1

        block_number = values[str(request_id)]
        time_stamp = self._w3.eth.getBlock(block_number).timestamp

        return time_stamp


class fork_process(Reader):
    def __init__(self, block_identifier = None) -> None:
        self.block_identifier = int(block_identifier)

        self.is_child = False
        self._baseConfig()

        self.init()

    def init(self):
        [
            etnyContract,
            currentBlock,
            startBlockNumber,
            values
        ] = self._action_args()

        itr = 0
        for i in range(self.block_identifier, self.block_identifier + BASE_LOOP_ITER, int(BASE_LOOP_ITER / 100)):
            currentCounter = self.insert(etnyContract=etnyContract, i=i)
            if itr >= 100:
                Database().commit()
                itr = 0
            itr += 1
            print('something here:d ', currentCounter,  i, self.block_identifier)

    def insert(self, etnyContract, i):
        currentCounter = etnyContract.functions._getDPRequestsCount().call(block_identifier=i)
        try:
            Database().insert(_id = currentCounter, order_id=i)
        except dbException as e:
            print('---' * 10)
            print('---' * 10)
            print(e)
            print('---' * 10)
            print('---' * 10)
            print('---' * 10)
            time.sleep(.01)
            self.insert(etnyContract=etnyContract, i=i)
        return currentCounter


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ethernity PoX request")
    parser.add_argument("-c", "--is_child", default=False)
    parser.add_argument("-b", "--block_identifier", default=0)
    parser = parser.parse_args()
    
    Reader(
        is_child=parser.is_child, 
        block_identifier=parser.block_identifier
    )