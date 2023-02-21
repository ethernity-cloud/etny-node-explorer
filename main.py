import os
import sys
import signal
import time
import traceback
from math import ceil
from typing import Union

from libs.base_class import BaseClass, IS_NOT_LINUX, config, Singleton, Database, \
    ABIFunctionNotFound  # pylint: disable=no-name-in-module
from models.dp_request_model import DPRequestModel
from libs.exceptions import ContinueFromLoopException, LastIterationException  # pylint: disable=no-name-in-module
from libs.generate_doc import CSVFileGenerator

PROCESS_COUNT = 30

if IS_NOT_LINUX:
    from threading import Thread as Process
    from _thread import interrupt_main
    from queue import Queue

    THREAD_DEAMON = True
else:
    from multiprocessing import Process, Queue

    THREAD_DEAMON = False


def signal_handler(sig, frame):  # pylint: disable=unused-argument,redefined-outer-name
    if len(GetDPRequests.results) > 0:
        print('resultsLen = ', len(GetDPRequests.results))
        GetDPRequests.store(models=GetDPRequests.results)
    if IS_NOT_LINUX:
        try:
            interrupt_main()
            os._exit()
        except:
            pass
    sys.exit()


for sig in [signal.SIGINT, signal.SIGTERM]:
    signal.signal(sig, signal_handler)


class InProcess(BaseClass, metaclass=Singleton):
    def __init__(self, w3=None, contract=None, parent_process_id=None) -> None:
        super().__init__()
        self.parent_process_id = parent_process_id
        self._baseConfig(w3=w3, contract=contract)

    def run_action(self, i, _input, output, _max=0, _iter_count=0):
        try:
            item = self.etnyContract.functions._getDPRequestWithCreationDate(
                i).call()  # pylint: disable=protected-access
            output.put(DPRequestModel([i, *item]))
        except ABIFunctionNotFound as err:
            method_name = str(err).split('The function')[1].split('was')[0].strip()
            print(f'\nabi method {method_name} was not found! ', self.parent_process_id)
            if IS_NOT_LINUX:
                os.kill(os.getpid(), signal.SIGTERM)
            else:
                os.killpg(self.parent_process_id, signal.SIGTERM)
            sys.exit(0)
        except Exception as err:
            if 'Connection aborted' in str(err) and _iter_count < PROCESS_COUNT:
                time.sleep(1)
                return self.run_action(i, _input=_input, output=output, _max=_max, _iter_count=_iter_count + 1)
            raise ContinueFromLoopException

    def run(self, _input, output, _max, _iter_count=0):  # pylint: disable=arguments-differ
        try:
            for dp_request_id in iter(_input.get, 'STOP'):
                _to = int(dp_request_id) + PROCESS_COUNT
                for i in range(int(dp_request_id), _max + 1 if _max < _to else _to):
                    try:
                        self.run_action(
                            i=i,
                            _input=_input,
                            output=output,
                            _max=_max,
                            _iter_count=_iter_count
                        )
                    except ContinueFromLoopException:
                        continue

        except Exception as err:
            print('\n process error', err)

    def run_for_missing_items(self, _input, output, _max=0, _iter_count=0):
        try:
            for dp_request_id in iter(_input.get, 'STOP'):
                try:
                    self.run_action(
                        i=int(dp_request_id),
                        _input=_input,
                        output=output,
                        _max=_max,
                        _iter_count=_iter_count
                    )
                except ContinueFromLoopException:
                    continue
        except Exception as err:
            print('\n process error', err)


class GetDPRequests(BaseClass):
    results = []
    current_dots_count = -1
    last_page_for_missing_records = 1

    def __init__(self) -> None:
        self._baseConfig()
        Database(config=config).init()

        self.init()

    @property
    def _get_max_block_number(self):
        try:
            return self._w3.eth.get_block('latest')['number']
        except Exception as ex:
            print("Can`t get block number, ", ex)
            sys.exit()

    @property
    def last_local_id(self) -> Union[int, None]:

        try:
            hours_back = int(config['DEFAULT'].get('HOURS_BACK', 24))
            average_block_time_in_seconds = float(config['DEFAULT'].get('AVERAGE_BLOCK_TIME_IN_SECONDS', 6.5))
            start_from_zero = bool(
                False if config['DEFAULT'].get('START_FROM_ZERO', 'False').lower() == 'false' else True)
        except Exception as ex:
            print('ex = ', ex)
            sys.exit(0)

        last_local_id = Database().get_last_dp_request()

        # when need to start from scratch
        if start_from_zero and last_local_id == None:
            return 0

        # compute last local id in relation to average block time in second 
        if last_local_id == None and not start_from_zero:
            nodes_back = int((hours_back * 60 * 60) // average_block_time_in_seconds)
            starting_block = int(self._get_max_block_number - nodes_back)
            last_local_id = self._max_id(starting_block=starting_block)
            self.last_page_for_missing_records = last_local_id

        if last_local_id > 0 and self.last_page_for_missing_records == 1 and not start_from_zero:
            min_dp_request_id = Database().get_min_dp_request_id()
            self.last_page_for_missing_records = min_dp_request_id

        return last_local_id

    def _max_id(self, starting_block=0):
        if starting_block == 0:
            return self.etnyContract.functions._getDPRequestsCount().call()  # pylint: disable=protected-access
        return self.etnyContract.functions._getDPRequestsCount().call(
            block_identifier=starting_block)  # pylint: disable=protected-access

    def init(self):
        last_local_id = self.last_local_id
        print('self.last_local_id = ', last_local_id, self.last_page_for_missing_records)

        self.display_percent()
        self.start(start_point=last_local_id if last_local_id else 0)

    @staticmethod
    def store(models):
        Database().store_dp_requests(models=models)

    def kill_proceses(self, task_queue, done_queue, jobs):
        try:
            task_queue.put('STOP')
            task_queue.close()
            done_queue.close()
            [i.kill() for i in jobs]  # pylint: disable=expression-not-assigned
        except Exception:
            pass

    def open_queue(self, process_call, _max):
        task_queue = Queue()
        done_queue = Queue()
        jobs = []
        for _ in range(PROCESS_COUNT):
            process = Process(target=process_call, args=(task_queue, done_queue, _max))
            process.daemon = THREAD_DEAMON
            jobs.append(process)
            process.start()

        return [task_queue, done_queue, jobs]

    def get_from_out_queue(self, _loop, done_queue):
        for _ in range(_loop):
            try:
                result = done_queue.get(timeout=10)
                GetDPRequests.results.append(result)
            except Exception as err:
                if '_queue.Empty' in str(type(err)):
                    break
                continue

        if len(GetDPRequests.results) >= PROCESS_COUNT:
            GetDPRequests.store(models=GetDPRequests.results)
            GetDPRequests.results = []

    def run_action(self, task_queue, done_queue, loop_iteration=0, loop_iters_count=0, callback=None) -> None:
        try:
            _iter = 0
            for i in loop_iteration:
                task_queue.put(i)

                _iter += 1
                if _iter and _iter % PROCESS_COUNT == 0:
                    if _iter % (PROCESS_COUNT * 2) == 0:
                        self.display_percent()
                    _loop = loop_iters_count
                    self.get_from_out_queue(_loop, done_queue)

                    if len(GetDPRequests.results) >= PROCESS_COUNT:
                        GetDPRequests.store(models=GetDPRequests.results)
                        GetDPRequests.results = []

            self.get_from_out_queue(loop_iters_count, done_queue)

            if len(GetDPRequests.results) > 0:
                GetDPRequests.store(models=GetDPRequests.results)
                GetDPRequests.results = []

            if callback:
                callback()

        except Exception as ex:
            print(traceback.format_exc(), type(ex))

    def start(self, total=0, start_point=0) -> None:
        _total = total if total else self._max_id()
        _max = _total
        loop_iteration = range(start_point, _max + 1, PROCESS_COUNT)
        [task_queue, done_queue, jobs] = self.open_queue(
            process_call=InProcess(contract=self.etnyContract, w3=self._w3, parent_process_id=os.getpid()).run,
            _max=_max
        )
        self.run_action(
            task_queue=task_queue,
            done_queue=done_queue,
            loop_iteration=loop_iteration,
            loop_iters_count=PROCESS_COUNT * PROCESS_COUNT,
            callback=(lambda: self.kill_proceses(task_queue=task_queue, done_queue=done_queue, jobs=jobs))
        )

        self.searching_for_missing_nodes(last_page=self.last_page_for_missing_records)

    def searching_for_missing_nodes(self, last_page=1, per_page=30, task_queue=None, done_queue=None, jobs=None):
        try:
            try:
                group_args = Database().get_missing_records(last_page=last_page, per_page=per_page)
                if group_args == None:
                    return
                group_args = group_args.split('-')

                for key, var in enumerate(group_args):
                    try:
                        group_args[key] = int(var)
                    except ValueError:
                        pass
                count, current_iter, _max, items = group_args
                if count == 0:
                    time.sleep(1)
                    raise ValueError
            except ValueError as ex:
                raise LastIterationException(ex)
            except AttributeError as ex:
                count = Database().get_missing_records_count()
                print('error here, last _page = ', last_page)
                if count:
                    return self.searching_for_missing_nodes()
                raise LastIterationException(f'count = 0')

            items = list(filter(lambda x: x, items.split(',')))
            # print(f'''\n
            #     count = {count} - {type(count)}, 
            #     current_iter = {current_iter} - {type(current_iter)}, 
            #     last_page = {last_page},
            #     _max = {_max} - {type(_max)}, 
            #     items = {items} - {type(items)}
            # ''')
            if not task_queue:
                [task_queue, done_queue, jobs] = self.open_queue(
                    process_call=InProcess(contract=self.etnyContract, w3=self._w3,
                                           parent_process_id=os.getpid()).run_for_missing_items,
                    _max=_max
                )
            self.display_percent()
            self.run_action(
                task_queue=task_queue,
                done_queue=done_queue,
                loop_iteration=items,
                loop_iters_count=PROCESS_COUNT,
                callback=(lambda: self.searching_for_missing_nodes(
                    last_page=current_iter,
                    task_queue=task_queue,
                    done_queue=done_queue,
                    jobs=jobs
                ))
            )

        except LastIterationException:
            self.kill_proceses(task_queue=task_queue, done_queue=done_queue, jobs=jobs)
            print('\ngenerate unique requests...')
            CSVFileGenerator()

    def display_percent(self):
        try:
            max_id = self._max_id()  # pylint: disable=protected-access
            currentMax = Database().get_count_of_dp_requests()
            if currentMax < self.last_local_id:
                currentMax = self.last_local_id
            percent = ceil((currentMax / max_id) * 100) if currentMax else 0
            message = f"Progress: {percent if (max_id - currentMax < 1000) else (percent - 1 if percent else 0)}%. Please wait"
            if GetDPRequests.current_dots_count >= 2:
                GetDPRequests.current_dots_count = -1
            GetDPRequests.current_dots_count += 1
            sys.stdout.write(f"\r{message}{''.join(map(lambda x: '.', list(range(GetDPRequests.current_dots_count))))}")
            sys.stdout.flush()
        except Exception:
            pass


if __name__ == '__main__':
    GetDPRequests()
