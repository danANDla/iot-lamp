#
# UNUSED
#

import multiprocessing
import time
from tgFrontend import AlarmBotFrontEnd
from tgBackend import AlarmBotBackEnd


def square_list(mylist, q):
    """
    function to square a given list
    """
    # append squares of mylist to queue
    time.sleep(5)
    for num in mylist:
        q.put(num * num)
    time.sleep(3)
    for num in mylist:
        q.put(num * num)


def print_queue(q):
    """
    function to print queue elements
    """
    print("Queue elements:")
    while not q.empty():
        print(q.get())
    print("Queue is now empty!")


def front(q):
    AlarmBotFrontEnd(q)


def back(q):
    AlarmBotBackEnd(q)


# if __name__ == "__main__":
#     # input list
#     mylist = [1, 2, 3, 4]
#
#     # creating multiprocessing Queue
#     q = multiprocessing.Queue()
#
#     # creating new processes
#     # p1 = multiprocessing.Process(target=square_list, args=(mylist, q))
#     # p2 = multiprocessing.Process(target=print_queue, args=(q,))
#     frontThread = multiprocessing.Process(target=front, args=(q,))
#     backThread = multiprocessing.Process(target=back, args=(q,))
#
#     # running process p1 to square list
#     frontThread.start()
#     frontThread.join()
#
#     # running process p2 to get queue elements
#     backThread.start()
#     backThread.join()
