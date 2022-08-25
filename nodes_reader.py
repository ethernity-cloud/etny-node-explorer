#!/usr/bin/python3

from platform import node
import multiprocessing, web3, argparse, sys, os, time, gc, asyncio
from packaging import version
from web3 import Web3
from web3.middleware import geth_poa_middleware
from node import Node
from multiprocessing import Process, Manager
from src.exceptions import DatabaseEngineNotFoundError
import config
from config import Database, dbException
from math import ceil
from typing import Tuple

from requests.exceptions import ConnectionError, HTTPError
from export_doc import CSVFileGenerator


logger = config.getLogger()

class sharedObject(object):
    def __init__(self):
        manager = Manager()
        self.val = manager.list()
        self.lock = multiprocessing.Lock()

    def append(self, value):
        with self.lock:
            if len(self.val) > config.LIMIT_OF_THREADS:
                self.val = []
            if value not in self.val:
                self.val.append(value)
    
    def reset(self):
        with self.lock:
            self.val = []

    @property
    def value(self):
        with self.lock:
            return self.val

GLOBAL_LOCK = multiprocessing.Lock()

class Reader:

    _w3 = None
    _contract = None
    _indexFile = None
    _nodesFile = None
    _httpProvider = None
    _firstContractTX = None

    def __init__(self, is_child = False, block_identifier = None) -> None:
        self.is_child = is_child
        self.block_identifier = block_identifier
        self._baseConfig()
        self.is_inline_process = True
        self.etnyContract = self._get_etnyContract()
        
        try:
            if self.is_child:
                self._childProcess()
            else:

                # Database().dropTable()

                # self.etnyContract = self._get_etnyContract()
                # do_count = self.etnyContract.caller()._getDORequestsCount()
                # dp_count = self.etnyContract.caller()._getDPRequestsCount()
                # print(do_count, dp_count)
                # return

                # init database
                Database(config=config.config, logger = logger).init()

                try:
                    self._mainLoop()    
                except HTTPError as e:
                    print(f"Server Address: {config.config['DEFAULT']['HttpProvider']} is Invalid. ")

        except KeyboardInterrupt as e:
            for process in multiprocessing.active_children():
                process.terminate()  
            print('\nRunning has been stopped by Ctrl-C')

    def _baseConfig(self) -> None:
        self._httpProvider = config.config['DEFAULT']['HttpProvider']
        self._contract = config.config['DEFAULT']['ContractAddress']
        self._indexFile = config.config['DEFAULT']['IndexFile']
        self._nodesFile = config.config['DEFAULT']['CSVFile']
        self._firstContractTX = config.config['DEFAULT']['firstContractTX']

        self._w3 = Web3(Web3.HTTPProvider(self._httpProvider))
        if version.parse(web3.__version__) < version.parse('5.0.0'):
            self._w3.middleware_stack.inject(geth_poa_middleware, layer=0)
        else:
            self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    def joinAll(self):
        logger.info("waiting for each process to be completed ...")
        for p in multiprocessing.active_children():
            p.join()

    def _loopContent(self, block_identifier = None, shared_object = None, _iter = 0, deamon = True, queryBlock = None, recursion_count = 0):

        #If active childrens count exceeds LIMIT_OF_THREADS, wait for any of them to be completed. 
        active_childrens_count = len(multiprocessing.active_children())
        if active_childrens_count > config.LIMIT_OF_THREADS - 1:
            logger.debug(f'process removal from the stack, Count of left processes: {active_childrens_count}')
            time.sleep(5 if recursion_count and recursion_count % 5 == 0 else 1)
            return self._loopContent(block_identifier, shared_object, _iter, queryBlock = queryBlock, recursion_count=recursion_count + 1)
        
        #Register/Run new Process
        thread = Process(target = fork_process, args = (block_identifier, shared_object, queryBlock))
        thread.daemon = deamon
        thread.start()

        # If necessary, free/refresh memory. if FREE_MEMORY_IN_INTERVAL is set to true.  
        if config.FREE_MEMORY_IN_INTERVAL:
            if _iter and _iter % int(config.BASE_LOOP_ITER / 2) == 0:
                self._free_memory(shared_object = shared_object)

    def _free_memory(self, shared_object = None):
        logger.info('need to join threads...')
        if shared_object:
            shared_object.reset()
            time.sleep(1)
        self.joinAll()
        gc.collect()
        time.sleep(1)   

    def generatorWrapper(self, callback = None, shared_object = None, with_block_identifiers = True, latestBlock = None):
        _iter = 1
        while True:
            try:
                blocks = self._getMissingRecords(limit=_iter)
                _iter += 1
                inline_counter = 0
                for block in blocks:
                    callback(block, with_block_identifiers)
                    inline_counter += 1

                    if config.FREE_MEMORY_IN_INTERVAL and inline_counter and inline_counter % int(config.BASE_LOOP_ITER / 2) == 0:
                        self._free_memory(shared_object = shared_object)

                    if _iter and _iter % 30 == 0:
                        self.display_percent()

                if not inline_counter:break
            except Exception as e:
                logger.error(f'generatorWrapper error: {str(e)}')
                break

    def display_percent(self):
        try:
            max_id = self.etnyContract.caller()._getDPRequestsCount()
            max_node = Database().select_one(single = 'max(id) as max')
            currentMax = 0
            count_of_missing_items = self.get_number_of_missing_items()
            if max_node:
                currentMax = max_node - count_of_missing_items          
            percent = ceil((currentMax / max_id) * 100) if currentMax else 0
            message = f"Progress: {percent}%. Please wait."
            sys.stdout.write(f"\r{message}")
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"displaying a percentage error: {str(e)}")
    
    def _mainLoop(self):
        [   
            currentBlockNumber,
            latestBlock
        ] = self._action_args()
        
        _iter = 0
        shared_object = sharedObject()

        # Main loop, starts from latest transaction
        for block_identifier in range(currentBlockNumber, latestBlock, config.BASE_LOOP_ITER):
            self._loopContent(block_identifier=block_identifier, shared_object=shared_object, _iter = _iter)
            if _iter % 10 == 0:
                self.display_percent()
            _iter += 1

        shared_object.reset()
        self.joinAll()
        logger.warning('------Searching for missing items, Please wait...')

        self.display_percent()

        # checking for missing records
        _iter = 0
        def wrapper(queryBlock, with_block_identifiers = True):
            ''' [real_id, missing_id_from, next_id, diff, block_identifier, next_block_identifier_and_diff] = block'''
            if len(queryBlock) < 4:return
            queryBlock = queryBlock + (with_block_identifiers,)
            self._loopContent(block_identifier=None, shared_object=shared_object, _iter = _iter, deamon=False, queryBlock = queryBlock)

        
        # Second loop - to get missing block items by the missing block numbers
        self.generatorWrapper(callback = wrapper, shared_object = shared_object, with_block_identifiers=True, latestBlock = latestBlock) # call with block identifiers and without

        # Third loop - to get missing block items by the missing id`s
        number_of_missing_items = self.get_number_of_missing_items()
        try_count = 0
        while number_of_missing_items > 0 and try_count < 10:
            self.generatorWrapper(callback = wrapper, shared_object = shared_object, with_block_identifiers=False, latestBlock = latestBlock) # call with block identifiers and without
            number_of_missing_items = self.get_number_of_missing_items()
            try_count += 1
        # Third loop

        self.display_percent()

        # Generate *.doc
        writer = CSVFileGenerator()
        # on finish

        logger.info('Completed all threads')

    def get_number_of_missing_items(self, recursion_count = 0):
        try:
            items_count = Database().number_of_missing_items()
        except dbException as e:
            if recursion_count > 10:
                return 0
            return self.get_number_of_missing_items(recursion_count=recursion_count+1)
        return items_count[0] if items_count else 0

    def _getMissingRecords(self, limit = 1):
        per_request = 10
        query = f'''select 
                        d.id as real_id,
                        (d.id + 1) as missing_id_from, 
                        (select min(id) from orders where id > d.id) as next_id,
                        ((select min(id) from orders where id > d.id) - (id + 1)) as diff,
                        d.block_identifier,
                        {Database().get_concatenated_fields()}
                    from orders d 
                    where d.id > -1 and not exists (select id from orders where id = d.id + 1) and d.id < (select max(id) from orders) 
                    limit {(limit - 1) * per_request if limit > 1 else 0}, {per_request}
                '''
        return Database().raw_select(query=query)
        
    def _get_etnyContract(self):
        return self._w3.eth.contract(address=self._contract, abi=self._get_contract_abi())

    def _action_args(self):
        try:  
            latestBlock = self._w3.eth.blockNumber
            max_node = Database().select_one(single = 'id, max(block_identifier) as max_block_identifier')
            if max_node:
                [_id, currentBlockNumber] = max_node
            else:
                firstBlockNumber = self._w3.eth.getTransaction(self._firstContractTX).blockNumber
                currentBlockNumber = firstBlockNumber + 10

            return [
                currentBlockNumber,
                latestBlock
            ]
        except (dbException, TypeError) as e:
            logger.error(f'-----{e}')
            time.sleep(0.01 if type(e) == TypeError else 5)
            return self._action_args()

    def _get_contract_abi(self) -> str:
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/entyContract.abi') as r:
                return r.read()
        except Exception as e:
            return None

class fork_process(Reader):
    local_buffer = set()
    shared_object = None
    queryBlock = None
    def __init__(self, block_identifier = None, shared_object = None, queryBlock = None) -> None:
        try:
            self.block_identifier = block_identifier
            self.shared_object = shared_object
            self.is_child = False
            self.queryBlock = queryBlock
            self._baseConfig()
            self.etnyContract = self._get_etnyContract()
            self.isDatabaseReconnected = False

            
            # if it is invoked from the second or third loop 
            if self.block_identifier == None and self.queryBlock != None:
                self.isDatabaseReconnected = True
                Database().reConnect(config=config.config)
                try:
                    [real_id, missing_id_from, next_id, diff, block_identifier, next_block_identifier_and_diff, with_block_identifiers] = self.queryBlock
                except ValueError as e:
                    logger.error(f'inline error {str(e)}', 'error')
                    sys.exit()
                [next_block_identifier, difference] = next_block_identifier_and_diff.split('-')
                if with_block_identifiers:
                    self._getMissingItemsByTheBlockIdentifier(
                        block_identifier=block_identifier, 
                        next_block_identifier = next_block_identifier
                    )
                else:
                    self._getMissingItemsById(
                        missing_id_from=missing_id_from,
                        next_id=next_id,
                        block_identifier=block_identifier
                    )
            else:
                # first, main loop
                self._getAllItems()
        except KeyboardInterrupt as e:
            pass

    def _getAllItems(self):
        itr = 0
        for block_identifier in range(self.block_identifier, self.block_identifier + config.BASE_LOOP_ITER, int(config.BASE_LOOP_ITER / 100)):
            self.insert(block_identifier=block_identifier)
            itr += 1

    # for missing items
    def _getMissingItemsByTheBlockIdentifier(self, block_identifier = None, next_block_identifier = None):
        for block_identifier in range(block_identifier, int(next_block_identifier), 2):
            self.insert(block_identifier=block_identifier)

    def _getMissingItemsById(self, missing_id_from = None, next_id = None, block_identifier = None):
        for currentCounter in range(missing_id_from, next_id):  
            self.insert(currentCounter=currentCounter, block_identifier=block_identifier)

    def insert(self, currentCounter = None, block_identifier = None, count_recursive_calls = 0):
        DELAY_IN_RECURSION_BETWEEN = 10
        display_exception_details = True
        insert_id = 0
        try:
            if not currentCounter:
                try:
                    currentCounter = self.etnyContract.functions._getDPRequestsCount().call(block_identifier=block_identifier)
                except ValueError as e: 
                    if count_recursive_calls % 5 == 0:
                        max_block_number = self._w3.eth.blockNumber
                        if block_identifier < max_block_number - 10:
                            block_identifier += 5
                            time.sleep(1)
                        display_exception_details = False
                        raise Exception(f'block is currently created: {block_identifier}, skipping...')
            try:
                insert_id = currentCounter if currentCounter != None and currentCounter > 0 else -1
                
                # inline buffer
                if insert_id in self.local_buffer:return
                if len(self.local_buffer) > 20:
                    self.local_buffer = set()
                
                # shared buffer
                if self.shared_object:
                    try:
                        if int(insert_id) in self.shared_object.value and not count_recursive_calls:return
                        # print('shared object = ', currentCounter, self.shared_object.value, count_recursive_calls, os.getpid())
                    except (ConnectionRefusedError, BrokenPipeError) as e:
                        logger.error(str(e))
                    
                if not self.isDatabaseReconnected:
                    Database().reConnect(config=config.config)
                if_exists = Database().select_one(single = 'id, block_identifier', id = insert_id)
                if not if_exists or (if_exists and if_exists[1] > block_identifier):
                    node = self._getNode(currentCounter, insert_id, block_identifier)
                    if not node:return
                    # with GLOBAL_LOCK:
                    _date = self._getTimestamp(block_identifier=block_identifier)
                    if not if_exists:
                        node.created_on = _date
                        Database().insert(node)
                    else:
                        node.last_updated = _date
                        Database().update(node).commit()
                    
            except dbException as e:
                self._getDetailedExceptionInfo()
                logger.error(f"'--* - {str(e)}, insert_id = {insert_id}")
                time.sleep(5)
                Database().reConnect(config = config.config)
                return self.insert(currentCounter = currentCounter, block_identifier=block_identifier)

            if self.shared_object:
                try:
                    self.shared_object.append(insert_id) # shared buffer
                except (ConnectionRefusedError, FileNotFoundError) as e:
                    time.sleep(.1)
                    logger.warning(f'The shared object has been blocked, insert_id: {insert_id}, {str(e)}')

            self.local_buffer.add(insert_id) # local buffer
            return insert_id

        except RecursionError as e:
            logger.error(f"RecursionError...")
            return
        except (ConnectionError, Exception) as e:
            
            if display_exception_details:
                self._getDetailedExceptionInfo()
                logger.error(f'- {block_identifier}, {e} {count_recursive_calls} {os.getpid()} {type(e)} - {insert_id}')
            else:
                logger.error(f'General Exception: {e}')

            if count_recursive_calls and count_recursive_calls % 10 == 0:
                time.sleep(1)

            self._baseConfig()
            self.etnyContract = self._get_etnyContract()
            if count_recursive_calls < 10:
                return self.insert(currentCounter=currentCounter, block_identifier = block_identifier, count_recursive_calls=count_recursive_calls + 1)

    def _getNode(self, currentCounter, insert_id, block_identifier) -> Tuple[Node, None]:
        request = self.etnyContract.functions._getDPRequest(currentCounter).call()
        if not request:
            logger.error("there no request at all ------")
            return None
                
        node = Node(
            id = insert_id,
            block_identifier = block_identifier
        )

        items = ['address', 'cpu', 'memory', 'storage', 'bandwith', 'duration', 'status', 'cost']
        for key, item in enumerate(items):
            try:
                setattr(node, item, request[key])
            except IndexError as e:
                pass
        return node

    def _getTimestamp(self, block_identifier, recursived_count = 0) -> int:
        try:
            timestamp = self._w3.eth.getBlock(block_identifier).timestamp
            if not timestamp and recursived_count < 10:
                return self._getTimestamp(block_identifier=block_identifier - 1, recursived_count=recursived_count + 1)
            return timestamp
        except Exception as e:
            logger.error('error while getting timestamp...')
        return int(time.time())

    def _getDetailedExceptionInfo(self):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.warning(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ethernity PoX request")
    parser.add_argument("-c", "--is_child", default=False)
    parser.add_argument("-b", "--block_identifier", default=0)
    parser = parser.parse_args()
    
    Reader(
        is_child=parser.is_child, 
        block_identifier=parser.block_identifier
    )   