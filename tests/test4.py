
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


class UsingWeb3():

    
    def __init__(self) -> None:
        super().__init__()
        
        print('first')
        self._baseConfig()
        print('second')
        self._action()

    def _baseConfig(self) -> None:
        config = configparser.ConfigParser()
        config.read(os.path.join(os.getcwd(), '../config.env'))
        self._httpProvider = config['DEFAULT']['HttpProvider']

        self._contract = config['DEFAULT']['ContractAddress']
        self._indexFile = config['DEFAULT']['IndexFile']
        self._nodesFile = config['DEFAULT']['CSVFile']

        self._w3 = Web3(Web3.HTTPProvider(self._httpProvider))
        self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)


    def _action(self):
        print('-------------ddd')
        self._w3 = Web3(Web3.HTTPProvider(self._httpProvider, session=session))
        self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.etnyContract = self._w3.eth.contract(address=self._contract, abi=self._read_contract_abi())
        firstContractTx = "0x90eeb0a0680034c8c340dfa60b773ed77b060d6a966596059610981486d312f4"
        print("Connected...")

        blockNumber = self._w3.eth.getTransaction(firstContractTx).blockNumber
        timestamp = self._w3.eth.getBlock(blockNumber).timestamp
        currentBlock = self._w3.eth.blockNumber

        print('block numberddddd', blockNumber)
        print('timestamp', timestamp)
        print('current block number', currentBlock)

   
    def _read_contract_abi(self) -> str:
        try:
            with open(os.path.join(os.getcwd(), '../entyContract.abi')) as r:
                return r.read()
        except Exception as e:
            return None



if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description="Ethernity PoX request")
    # parser.add_argument("-c", "--is_child", default=False)
    # parser = parser.parse_args()
    # withProcess(is_child = parser.is_child)

    u = UsingWeb3()
    print('----------before')
    for item in [12867544, 12867545, 12867546, 12867547, 12867548, 12867549, 12867550, 12867551, 12867552]:
        result = u.etnyContract.functions._getDPRequestsCount().call(block_identifier=item)
        print(result)
    print('----------after')

    sys.exit()

    for _block_identifier in l:
        self._loopContent(block_identifier=_block_identifier, shared_object=shared_object, _iter = _iter, next_block_identifier = next_block_identifier)


