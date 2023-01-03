import time
import random, os

from multiprocessing import Process, Queue, current_process, freeze_support

#
# Function run by worker processes
#

def worker(input, output):
    for args in iter(input.get, 'STOP'):
        print(os.getpid(), ' ', args)
        result = args
        output.put(result)
        time.sleep(3)
        

#
# Function used to calculate result
#

def calculate(func, args):
    result = func(*args)
    return '%s says that %s%s = %s' % \
        (current_process().name, func.__name__, args, result)

#
# Functions referenced by tasks
#

def mul(a, b):
    return a * b

def plus(a, b):
    return a + b

#
#
#

def test():
    NUMBER_OF_PROCESSES = 20
    TASKS1 = [i for i in range(30)]

    # Create queues
    task_queue = Queue()
    done_queue = Queue()

    # Submit tasks
    for task in TASKS1:
        task_queue.put(task)
    
    for task in TASKS1:
        task_queue.put(task)

    # Start worker processes
    for i in range(NUMBER_OF_PROCESSES):
        Process(target=worker, args=(task_queue, done_queue)).start()

    

    # Get and print results
    print('Unordered results:')
    for i in range(len(TASKS1)):
        print('\t', done_queue.get())
    time.sleep(3)

    for i in range(len(TASKS1)):
        print('\t', done_queue.get())


    # Tell child processes to stop
    # for i in range(NUMBER_OF_PROCESSES):
    #     task_queue.put('STOP')
    
if __name__ == '__main__':
    # freeze_support()
    test()