
import os, sys, time, asyncio, requests, argparse
from threading import Thread
from multiprocessing import Process, Pool
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.eth import AsyncEth
import configparser


adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
session = requests.Session()
session.mount('http://', adapter)
session.mount('https://', adapter)

sys.path.extend([os.path.join(os.getcwd(), '../')])


num = 1

connection_string = '''curl -X GET "https://blockexplorer.bloxberg.org/api?module=account&action=balance&address={contractAddress}"'''
class UsingWeb3():

    
    def __init__(self) -> None:
        super().__init__()
        
    def action(self):
        os.system(connection_string)
        print('\n')

    ################################## 1
    async def asyncAction(self):
        response = await asyncio.create_subprocess_shell(connection_string, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        stdout, stderr = await response.communicate()
        print(stdout.decode())

    def asyncRun(self):
        asyncio.run(self.asyncAction())
    ################################## 1

    async def asyncWeb3(self):
        self._contract = self._contract
        w3  = Web3(Web3.AsyncHTTPProvider('https://core.bloxberg.org'), modules={"eth": [AsyncEth]}, middlewares=[])
        firstContractTx = "0x90eeb0a0680034c8c340dfa60b773ed77b060d6a966596059610981486d312f4"
        print("Connected...")
        _blockNumber =  await w3.eth.get_transaction(firstContractTx)
        blockNumber = _blockNumber.blockNumber
        _timestamp = await w3.eth.get_block(blockNumber)
        timestamp = _timestamp.timestamp
        currentBlock = await w3.eth.block_number
        print(blockNumber)
        print(timestamp)
        print(currentBlock)
        print('before error....')
        currentBlock = w3.eth.blockNumber


        currentCounter = etnyContract.functions._getDPRequestsCount().call(block_identifier=blockNumber)
        print(currentCounter)

        await asyncio.sleep(1)

    ############################

    def __action(self, etnyContract, i):
        try:
            currentCounter = etnyContract.functions._getDPRequestsCount().call(block_identifier=i)
            print(currentCounter, i)
        except Exception as e:
            print(e)

    def _action(self):
        self._w3 = Web3(Web3.HTTPProvider(self._httpProvider, session=session))
        self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        etnyContract = self._w3.eth.contract(address=self._contract, abi=self._read_contract_abi())
        firstContractTx = "0x90eeb0a0680034c8c340dfa60b773ed77b060d6a966596059610981486d312f4"
        print("Connected...")

        blockNumber = self._w3.eth.getTransaction(firstContractTx).blockNumber
        timestamp = self._w3.eth.getBlock(blockNumber).timestamp
        currentBlock = self._w3.eth.blockNumber

        print('block numberddddd', blockNumber)
        print('timestamp', timestamp)
        print('current block number', currentBlock)

        startBlockNumber = blockNumber + 10
        _iter = 0
        for i in range(startBlockNumber, currentBlock, 10):

            # self.__action(etnyContract, i)
            t = Process(target = self.__action, args = (etnyContract, i)).start()
            
            if _iter > 2:break
            _iter += 1

    def _read_contract_abi(self) -> str:
        try:
            with open(os.path.join(os.getcwd(), '../entyContract.abi')) as r:
                return r.read()
        except Exception as e:
            return None


class mainProcess:
    def __init__(self) -> None:

        for i in range(20):
            t = Process(target = self.init, args = ())
            t.start()
            # self.init()

    def init(self):
        asyncio.run(self.action(cmd = 'python3 test3.py -c True'))

    async def action(self, cmd = ''):
        inlineProc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        stdout, stderr = await inlineProc.communicate()
        print(stdout.decode())

class withProcess(UsingWeb3):
     
    def __init__(self, is_child = False) -> None:
        # if is_child:    
        #     print('there we aredddd')
        #     self.inProcess()
        # else:
        #     mainProcess()

        for i in range(20):
            t = Process(target = self.inProcess, args = ())
            t.start()


    def _baseConfig(self) -> None:
        config = configparser.ConfigParser()
        config.read(os.path.join(os.getcwd(), '../config.env'))
        self._httpProvider = config['DEFAULT']['HttpProvider']

        self._contract = config['DEFAULT']['ContractAddress']
        self._indexFile = config['DEFAULT']['IndexFile']
        self._nodesFile = config['DEFAULT']['CSVFile']

        self._w3 = Web3(Web3.HTTPProvider(self._httpProvider))
        self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    def inProcess(self):
        self._baseConfig()
        etnyContract = self._w3.eth.contract(address=self._contract, abi=self._read_contract_abi())
        firstContractTx = "0x90eeb0a0680034c8c340dfa60b773ed77b060d6a966596059610981486d312f4"

        blockNumber = self._w3.eth.getTransaction(firstContractTx).blockNumber
        timestamp = self._w3.eth.getBlock(blockNumber).timestamp
        currentBlock = self._w3.eth.blockNumber
        startBlockNumber = blockNumber + 10

        try:
            currentCounter = etnyContract.functions._getDPRequestsCount().call(block_identifier=startBlockNumber)
            print(currentCounter)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ethernity PoX request")
    parser.add_argument("-c", "--is_child", default=False)
    parser = parser.parse_args()
    withProcess(is_child = parser.is_child)


'''
print(Database().select_one(single = 'id', order_id = 16629033, id = 87098))
print('-------')
for item in Database().select_all(single = 'id'):
    print(item)

l = Database().select_one(single = 'id', id = 87030)
print('dd1', l)
l = Database().select_one(id = 87030)
print('dd2', l)
# print(Database().select_all())

# print(Database().count(id = 87110))
# print(Database().count())

'''
