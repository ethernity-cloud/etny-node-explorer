
from threading import Thread
from multiprocessing import Process, Pool, Queue
import random, os

import time, asyncio
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.eth import AsyncEth
from aiohttp import ClientSession
import requests


adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
session = requests.Session()
session.mount('http://', adapter)
session.mount('https://', adapter)

from nodes_reader import Reader

num = 1

connection_string = '''curl -X GET "https://blockexplorer.bloxberg.org/api?module=account&action=balance&address={contractAddress}"'''
class Child(Reader):

    
    def __init__(self) -> None:
        super().__init__()



        self._action()

        for i in range(num):
            # self.action(etnyContract, i)
            # t = Process(target = self.action).start()
            #self.asyncRun()

            # asyncio.run(self.asyncWeb3())

            #self._action()

            pass

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
        etnyContract = self._w3.eth.contract(address=self._contract, abi=self.__read_contract_abi())
        firstContractTx = "0x90eeb0a0680034c8c340dfa60b773ed77b060d6a966596059610981486d312f4"
        print("Connected...")

        blockNumber = self._w3.eth.getTransaction(firstContractTx).blockNumber
        timestamp = self._w3.eth.getBlock(blockNumber).timestamp
        currentBlock = self._w3.eth.blockNumber

        print('block number', blockNumber)
        print('timestamp', timestamp)
        print('current block number', currentBlock)

        startBlockNumber = blockNumber + 10
        _iter = 0
        for i in range(startBlockNumber, currentBlock, 10):

            # self.__action(etnyContract, i)
            t = Process(target = self.__action, args = (etnyContract, i)).start()


            if _iter > 5:break
            _iter += 1

    def __read_contract_abi(self) -> str:
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/entyContract.abi') as r:
                return r.read()
        except Exception as e:
            return None

if __name__ == '__main__':
    Child()

