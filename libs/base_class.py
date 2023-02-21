# pylint: disable=unused-import,ungrouped-imports
import sys
import os 
from web3 import Web3, __version__ as web3_version
from web3.exceptions import ABIFunctionNotFound
from packaging import version
from web3.middleware import geth_poa_middleware
from config import config, Singleton, Database, IS_NOT_LINUX

class BaseClass:
    def _baseConfig(self, w3 = None, contract = None) -> None:
        # pylint: disable=attribute-defined-outside-init, invalid-name
        self._httpProvider = config['DEFAULT']['HttpProvider']
        self._contract = config['DEFAULT']['ContractAddress']
        self._indexFile = config['DEFAULT']['IndexFile']
        self._nodesFile = config['DEFAULT']['CSVFile']
        self._firstContractTX = config['DEFAULT']['firstContractTX']

        if w3:
            self._w3 = w3
        else:
            self._w3 = Web3(Web3.HTTPProvider(self._httpProvider))
            if version.parse(web3_version) < version.parse('5.0.0'):
                self._w3.middleware_stack.inject(geth_poa_middleware, layer=0)
            else:
                self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        self.etnyContract = contract if contract else self._get_etny_contract()
        
    def _get_etny_contract(self):
        return self._w3.eth.contract(address=self._contract, abi=self._get_contract_abi())

    def _get_contract_abi(self) -> str:
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/../etnyContract.abi') as r: # pylint: disable=unspecified-encoding
                return r.read()
        except Exception:
            return None

    def run(self):
        pass