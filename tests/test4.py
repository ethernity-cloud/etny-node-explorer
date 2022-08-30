
import os, sys, time, asyncio, requests, argparse
from tabnanny import check
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

    
    def __init__(self, httpProvider = None) -> None:
        super().__init__()
        
        self._baseConfig(httpProvider)
        self._action()

    def _baseConfig(self, httpProvider = None) -> None:
        config = configparser.ConfigParser()
        config.read(os.path.join(os.getcwd(), '../config.env'))
        self._httpProvider = httpProvider if httpProvider else config['DEFAULT']['HttpProvider']

        self._contract = config['DEFAULT']['ContractAddress']
        self._indexFile = config['DEFAULT']['IndexFile']
        self._nodesFile = config['DEFAULT']['CSVFile']

        self._w3 = Web3(Web3.HTTPProvider(self._httpProvider))
        self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)


    def _action(self):
        self._w3 = Web3(Web3.HTTPProvider(self._httpProvider, session=session))
        self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.etnyContract = self._w3.eth.contract(address=self._contract, abi=self._read_contract_abi())
        firstContractTx = "0x90eeb0a0680034c8c340dfa60b773ed77b060d6a966596059610981486d312f4"
    
        blockNumber = self._w3.eth.getTransaction(firstContractTx).blockNumber
        timestamp = self._w3.eth.getBlock(blockNumber).timestamp
        currentBlock = self._w3.eth.blockNumber

    def _read_contract_abi(self) -> str:
        try:
            with open(os.path.join(os.getcwd(), '../entyContract.abi')) as r:
                return r.read()
        except Exception as e:
            return None


def check_all(url, tryCount = 0):
    try:
        u = UsingWeb3(httpProvider=url)
    except (requests.exceptions.InvalidSchema, requests.exceptions.ConnectionError) as e:
        print('error = ',e, url)
        if tryCount == 0:
            return check_all(url = f"http://{url.split('@')[1]}", tryCount=1)
        elif tryCount == 1:
            return check_all(url = f"https://{url.split('http://')[1]}", tryCount=2)

if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description="Ethernity PoX request")
    # parser.add_argument("-c", "--is_child", default=False)
    # parser = parser.parse_args()
    # withProcess(is_child = parser.is_child)
    import requests,re
    r = requests.get('https://github.com/bloxberg-org/bloxbergValidatorSetup/blob/master/validator/bootnodes.txt')
    content = r.content.decode()
    links = re.findall("<td(.*?)>((.*?))</td>", content)
    urls = []
    for link in links:
        if '#' not in link[1] and '//' in link[1]:
            urls.append(link[1])
    check_all('https://130.183.206.234  ')
    sys.exit()
    for url in urls:
        check_all(url)



    sys.exit()
    print('----------before')
    for item in [12867544, 12867545, 12867546, 12867547, 12867548, 12867549, 12867550, 12867551, 12867552]:
        result = u.etnyContract.functions._getDPRequestsCount().call(block_identifier=item)
        print(result)
    print('----------after')


    for _block_identifier in l:
        self._loopContent(block_identifier=_block_identifier, shared_object=shared_object, _iter = _iter, next_block_identifier = next_block_identifier)


