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
config = configparser.ConfigParser()
config.read('config.env')
httpProvider = config['DEFAULT']['HttpProvider']
contract = config['DEFAULT']['ContractAddress']
indexFile = config['DEFAULT']['IndexFile']
nodesFile = config['DEFAULT']['CSVFile']

w3 = Web3(Web3.HTTPProvider(httpProvider))
if version.parse(web3.__version__) < version.parse('5.0.0'):
    w3.middleware_stack.inject(geth_poa_middleware, layer=0)
else:
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)


def read_contract_abi():
    try:
        contract_file = open(os.path.dirname(os.path.realpath(__file__)) + '/entyContract.abi')
        abi = contract_file.read()
        contract_file.close()
        return abi
    except Exception as e:
        print(e)
        return None


def read_index_content():
    index_dict = dict()
    if os.path.exists(indexFile):
        index = open(indexFile)
        index_dict = json.load(index)
        index.close()

    return index_dict


def read_csv_file(file):
    _rows = dict()
    if not os.path.exists(file):
        return _rows

    with open(file) as fileContent:
        for line in csv.reader(fileContent, dialect="excel-tab"):
            _row = Node(line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7], line[8], line[9],
                        line[10])
            _rows[_row.address] = _row

    return _rows


etnyContract = w3.eth.contract(address=contract, abi=read_contract_abi())
firstContractTx = "0x90eeb0a0680034c8c340dfa60b773ed77b060d6a966596059610981486d312f4"
print("Connected to: ", httpProvider)

blockNumber = w3.eth.getTransaction(firstContractTx).blockNumber
timestamp = w3.eth.getBlock(blockNumber).timestamp
currentBlock = w3.eth.blockNumber

print('block number', blockNumber)
print('timestamp', timestamp)
print('current block number', currentBlock)

values = read_index_content()
startBlockNumber = blockNumber + 10
if len(values.keys()) > 0:
    startBlockNumber = values[max(values, key=values.get)]

for i in range(startBlockNumber, currentBlock, 10):
    currentCounter = etnyContract.functions._getDPRequestsCount().call(block_identifier=i)
    if currentCounter not in values:
        values[currentCounter] = i
        if currentCounter % 10 == 0:
            with open(indexFile, 'w') as convert_file:
                convert_file.write(json.dumps(values))
    print('reading block: ', i)

with open(indexFile, 'w') as convert_file:
    convert_file.write(json.dumps(values))

nodes = read_csv_file(nodesFile)

startingCount = 0
if len(nodes.keys()) > 0:
    startingCount = etnyContract.functions._getDPRequestsCount().call(block_identifier=startBlockNumber)

endingCount = etnyContract.functions._getDPRequestsCount().call()


def get_timestamp_from_request(request_id):
    while str(request_id) not in values.keys():
        request_id = request_id - 1

    block_number = values[str(request_id)]
    time_stamp = w3.eth.getBlock(block_number).timestamp

    return time_stamp


node_index = len(nodes.keys()) + 1
for i in range(startingCount, endingCount):
    request = etnyContract.functions._getDPRequest(i).call()
    print("reading request ", i)
    if request[0] not in nodes:
        node = Node(node_index, request[0], request[1], request[2], request[3], request[4], request[5], request[6],
                    request[7],
                    get_timestamp_from_request(i), get_timestamp_from_request(i))
        nodes[request[0]] = node
        node_index = node_index + 1
    else:
        nodes[request[0]].last_updated = get_timestamp_from_request(i)

if len(nodes) > 0:
    with open(nodesFile, 'w',
              newline='') as output_file:
        writer = csv.writer(output_file, dialect="excel-tab")
        for k, row in nodes.items():
            writer.writerow(
                [row.no, row.address, row.cpu, row.memory, row.storage, row.bandwith, row.duration, row.status,
                 row.cost, row.created_on, row.last_updated])
