#!/usr/bin/python3

from packaging import version
import web3

import configparser
import os
from web3 import Web3
import json
from web3.middleware import geth_poa_middleware
import csv
from node import Node

# config section

class NotFoundException(Exception):
    pass

class Reader:

    _w3 = None
    _contract = None
    _indexFile = None
    _nodesFile = None

    def __init__(self) -> None:
        self._baseConfig()


        self._action()

    def _baseConfig(self) -> None:
        config = configparser.ConfigParser()
        config.read('config.env')
        httpProvider = config['DEFAULT']['HttpProvider']

        self._contract = config['DEFAULT']['ContractAddress']
        self._indexFile = config['DEFAULT']['IndexFile']
        self._nodesFile = config['DEFAULT']['CSVFile']

        self._w3 = Web3(Web3.HTTPProvider(httpProvider))
        if version.parse(web3.__version__) < version.parse('5.0.0'):
            self._w3.middleware_stack.inject(geth_poa_middleware, layer=0)
        else:
            self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    def _action(self):
        etnyContract = self._w3.eth.contract(address=self._contract, abi=self.__read_contract_abi())
        firstContractTx = "0x90eeb0a0680034c8c340dfa60b773ed77b060d6a966596059610981486d312f4"
        print("Connected...")

        blockNumber = self._w3.eth.getTransaction(firstContractTx).blockNumber
        timestamp = self._w3.eth.getBlock(blockNumber).timestamp
        currentBlock = self._w3.eth.blockNumber

        print('block number', blockNumber)
        print('timestamp', timestamp)
        print('current block number', currentBlock)

        values = self.__read_index_content()
        startBlockNumber = blockNumber + 10
        if len(values.keys()) > 0:
            startBlockNumber = values[max(values, key=values.get)]

        for i in range(startBlockNumber, currentBlock, 10):
            currentCounter = etnyContract.functions._getDPRequestsCount().call(block_identifier=i)
            if currentCounter not in values:
                values[currentCounter] = i
                if currentCounter % 10 == 0:
                    with open(self._indexFile, 'w') as convert_file:
                        convert_file.write(json.dumps(values))
            print('reading block: ', i)

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
                    writer.writerow(
                        [row.no, row.address, row.cpu, row.memory, row.storage, row.bandwith, row.duration, row.status,
                        row.cost, row.created_on, row.last_updated])

    def __read_contract_abi(self) -> str:
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/entyContract.abi') as r:
                return r.read()
        except Exception as e:
            return None

    def __read_index_content(self) -> dict:
        if os.path.exists(self._indexFile):
            with open(self._indexFile) as r:
                return json.loads(r)
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



if __name__ == '__main__':
    Reader()