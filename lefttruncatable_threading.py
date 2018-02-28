"""
lefttruncatable.py is written to print out all left-truncatable primes.
According to "Truncatable prime" in
https://en.wikipedia.org/wiki/Truncatable_prime,
there are 4260 decimal left-truncatable primes.

The multithreading mechanism is referenced from
http://www.tutorialspoint.com/python/python_multithreading.htm

Check out multiprocessing from
https://docs.python.org/3.5/library/multiprocessing.html
"""

import time
import math
import sys
import os
import queue
import threading
import multiprocessing as mp
from multiprocessing import Queue

# Parameters
INIT_MILESTONE_INCREMENT = 100      # We report a milestone when we found
                                    # MILESTONE_INCREMENT more left
                                    # truncatable primes.
NUM_LAST_LEFTTRNCPRIMES_TO_PRINT = 10   # Number of the largest (found) left trunctable primes to print.
SLEEP_WAITING_TIME = 2              # Number of seconds to wait before we check whether
                                    # threadPool is empty.
                                    
# Classes and Functions
class myThread(threading.Thread):
    # Constructor for myThread
    def __init__(self, threadID, q, leftTruncatables, threadBusy):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.q = q
        self.leftTruncatables = leftTruncatables
        self.threadBusy = threadBusy

    def run(self):
        process_data(self.threadID, self.q, self.leftTruncatables, self.threadBusy)


def is_prime(x):
    """
    is_prime() tests if the given argument x is a prime.  It does not
    perform checks like whether x is an integer, etc.
    """

    if x > 100000:
        return False
    
    # Check if x is a multiple of 3
    if x % 3 == 0:
        return False

    # x is odd and it is not a multiple of 3.  We check if x can be
    # divided by another integer by trying divisor_candidate of the
    # form (30k+m) and with k and m being an integer and see if x is
    # one of divisor_candidate's multiples.  If x is found to be a
    # multiple of such divisor_candidate's, the loop can end.
    x_isprime = True
    divisor_candidate = 7
    while True:
        if divisor_candidate*divisor_candidate > x:
            break
        # 7, 11, 13 and 17
        if (x % divisor_candidate == 0) or \
           (x % (divisor_candidate + 4) == 0) or \
           (x % (divisor_candidate + 6) == 0) or \
           (x % (divisor_candidate + 10) == 0):
            x_isprime = False
            break
        if (divisor_candidate + 12)*(divisor_candidate + 12) > x:
            break
        # 19, 23, 29 and 31
        if (x % (divisor_candidate + 12) == 0) or \
           (x % (divisor_candidate + 16) == 0) or \
           (x % (divisor_candidate + 22) == 0) or \
           (x % (divisor_candidate + 24) == 0):
            x_isprime = False
            break
        divisor_candidate += 30

    return x_isprime

def process_data(threadID, q, leftTruncatables, threadBusy):
    while not threadsExitFlag:
        if not q.empty():
            queueLock.acquire()
            left_truncatable_candidate = q.get()
            queueLock.release()
            threadBusy[threadID] = True         # This thread has job to do.

            # left truncatable primes contain no 0, so we want to check if
            # we obtain another left truncatable prime by prepending a nonzero
            # digit to its left.
            next_power10 = 1
            while next_power10 <= left_truncatable_candidate:
                next_power10 *= 10
            for i in range(1, 10):
                left_truncatable_candidate += next_power10
                if is_prime(left_truncatable_candidate):
                    global milestone_increment, next_milestone      # We want to modify the
                                        # global copies of these two variables so the other
                                        # threads will be notified.  Note that now several threads
                                        # are working together, so the left truncatable primes
                                        # found would not be in the same order as we had before
                                        # with single thread.
                    queueLock.acquire()
                    q.put(left_truncatable_candidate)
                    leftTruncatables.append(left_truncatable_candidate)
                    lenLeftTruncatalbes = len(leftTruncatables)
                    queueLock.release()
                    if lenLeftTruncatalbes == next_milestone:
                        queueLock.acquire()
                        print('Milestone %d: %d' % (next_milestone, left_truncatable_candidate))
                        if next_milestone == 4000:
                            milestone_increment = 10
                        if next_milestone == 4200:
                            milestone_increment = 1
                        next_milestone += milestone_increment
                        queueLock.release()
            threadBusy[threadID] = False        # This thread is done and would like
                                                # a vacation.
        # Waiting for one second before this thread checks threadsExitFlag again.
        time.sleep(1)

def anyThreadsBusy(threadBusy):
    """
    anyThreadsBusy() checks if any thread is busy.  All threads being idle indicates
    the threads might have run out of tasks to do.
    """
    for threadStatus in threadBusy:
        if threadStatus:
            return True
    return False


def anyProcsBusy(procBusy):
    """
    anyProcsBusy() checks if any process is busy as indicated by procBusy[].
    All processes being idle indicates the processes might have run out of
    tasks to work on.
    """
    for procStatus in procBusy:
        if procStatus:
            return True
    return False


def process_cand(left_truncatable_candidate, cand_queue, foundLeftTruncatables, threadPool,
                 milestone_increment, next_milestone):
    """
    process_cand() picks up a candidate from cand_queue, and then check if we can derive
    more left truncatable primes.  process_cand() is also responsible to update the related
    lists.
    """
    # Acquiring left_truncatable_candiate from cand_queue.
    queueLock.acquire()
    process_pid = os.getpid()
    threadPool.append(process_pid)
    queueLock.release()

    if left_truncatable_candidate:
        # We have a candidate.  Derive the 9 possible candidates from this candidate.
        # next_power10 corresponds to the next digit '1' appended to left of
        # left_truncatable_candidate.
        next_power10 = 1
        while next_power10 <= left_truncatable_candidate:
            next_power10 *= 10

        for i in range(1, 10):
            left_truncatable_candidate += next_power10

            if is_prime(left_truncatable_candidate):
                # We found a new left truncatable prime.
                queueLock.acquire()
                cand_queue.put(left_truncatable_candidate)
                foundLeftTruncatables.append(left_truncatable_candidate)

                # Decide if we want to print an update of the left ttuncatable prime hunting.
                next_ms_value = next_milestone.value
                if len(foundLeftTruncatables) == next_ms_value:
                    print('Milestone %d: %d' % (next_ms_value, left_truncatable_candidate))
                    ms_delta = milestone_increment.value
                    if next_ms_value == 4000:
                        ms_delta = 10
                    if next_ms_value == 4200:
                        ms_delta = 1
                    next_ms_value += ms_delta
                    next_milestone.value = next_ms_value
                    milestone_increment.value = ms_delta
                queueLock.release()

    # We are done.  Removing PID from threadPool
    queueLock.acquire()
    threadPool.remove(process_pid)
    queueLock.release()


def process_cand1(procID, cand_queue, foundLeftTruncatables, procBusy,
                  milestone_increment, next_milestone):
    """
    process_cand1() picks up a candidate from cand_queue, and then check if we can derive
    more left truncatable primes.  process_cand() is also responsible to update the related
    lists.
    """

    # We break out of the loop when there is nothing in the candidate
    # queue, and other processes are not busy.  We need both conditions
    # because it is possible one process is checking whether a candidate
    # leads to new left truncatable primes, and we do not want to exit
    # this process because that candidate can lead to more candidates later.
    while (not cand_queue.empty()) or anyProcsBusy(procBusy):
        # Acquiring left_truncatable_candiate from cand_queue.
        queueLock.acquire()
        try:
            left_truncatable_candidate = cand_queue.get_nowait()
            # Setting the process to busy if we successfully grabbed
            # left_truncatable_candidate.
            procBusy[procID] = True
        except:
            left_truncatable_candidate = None
        queueLock.release()

        if left_truncatable_candidate:
            # We have a candidate.  Derive the 9 possible candidates from this candidate.
            # next_power10 corresponds to the next digit '1' appended to left of
            # left_truncatable_candidate.
            next_power10 = 1
            while next_power10 <= left_truncatable_candidate:
                next_power10 *= 10

            for i in range(1, 10):
                left_truncatable_candidate += next_power10

                if is_prime(left_truncatable_candidate):
                    # We found a new left truncatable prime.
                    queueLock.acquire()
                    cand_queue.put(left_truncatable_candidate)
                    foundLeftTruncatables.append(left_truncatable_candidate)

                    # Decide if we want to print an update of the left ttuncatable prime hunting.
                    # Note that left(foundLeftTruncatables) only gives a rough estimate of the
                    # queue length, so we can no longer print something based on an equality check.
                    next_ms_value = next_milestone.value
                    if len(foundLeftTruncatables) >= next_ms_value:
                        print('Milestone %d: %d' % (next_ms_value, left_truncatable_candidate))
                        ms_delta = milestone_increment.value
                        if next_ms_value == 4000:
                            ms_delta = 10
                        if next_ms_value == 4200:
                            ms_delta = 1
                        next_ms_value += ms_delta
                        next_milestone.value = next_ms_value
                        milestone_increment.value = ms_delta
                    queueLock.release()

            # We are done.  Indicating this process is no longer busy.  This is not
            # protected by locks because in theory different processes won't access
            # the same procBusy[].
            procBusy[procID] = False

        else:
            # Wait before checking the exiting conditions again.
            time.sleep(SLEEP_WAITING_TIME)

    # We break out of the while loop, meaning cand_queue is empty *AND*
    # all processes are idling.

    
# Global variables
threadsExitFlag = False
queueLock = threading.Lock()
milestone_increment = INIT_MILESTONE_INCREMENT
next_milestone = milestone_increment

def main_threading():
    """
    main() to generate a list of left truncatable primes.
    """

    # Printing version info about imported modules.  The other modules do not
    # provide .__version__ info.
    # print('==== multiprocessing module version ' + multiprocessing.__version__ + ' ====')

    # Check out more information about Python multiprocessing in
    # https://docs.python.org/2/library/multiprocessing.html.
    numLogicalProcessors = multiprocessing.cpu_count()
    
    # The list foundLeftTruncatables starts with all the single-digit primes,
    # and they happen to be left-truncatable primes as well.
    foundLeftTruncatables = [2, 3, 5, 7]

    # Create new threads.  Refer to https://docs.python.org/2/library/queue.html for
    # information about queue.
    leftTruncatableSeedsQueue = queue.Queue(0)  # There is no size limit for the queue
                                    # because we do not know in advance how many left
                                    # truncatable primes are waiting to be extended.
    threadsPool = []
    threadBusy = [False] * numLogicalProcessors

    queueLock.acquire()
    # There is no way to generate new foundLeftTruncatables by prepending digits
    # to 2 and 5.  This implies is_prime(x) does not need to test divisibility
    # against 2 and 5, and we start with 3 and 7.
    leftTruncatableSeedsQueue.put(3)
    leftTruncatableSeedsQueue.put(7)
    queueLock.release()

    # Once the threads are created, they start working.  start() will call run().
    start_time = time.time()
    for i in range(0, numLogicalProcessors):
        thread = myThread(i, leftTruncatableSeedsQueue, foundLeftTruncatables, threadBusy)
        thread.start()
        threadsPool.append(thread)

    # We break out of the infinite loop when all threads are idling, and
    # there is nothing in leftTruncatableSeeds queue.
    while anyThreadsBusy(threadBusy) or (not leftTruncatableSeedsQueue.empty()):
        pass

    elapsed_time = time.time() - start_time

    # Notifying all threads it is time to exit.  We modify threadsExitFlag, and need to
    # declare it as global so process_data() will read True.
    global threadsExitFlag
    threadsExitFlag = True

    # Wait for all threads to finish
    for t in threadsPool:
        t.join()

    # Now sort the left_truncatable list before printing.
    foundLeftTruncatables.sort()

    # Printing some information.
    print('\nWe found %d left-truncatable primes so far in %0.4f seconds.' \
          % (len(foundLeftTruncatables), elapsed_time))
    print("The largest left-truncatable primes are:")
    for left_truncatable in foundLeftTruncatables[-NUM_LAST_LEFTTRNCPRIMES_TO_PRINT:]:
        print(left_truncatable)
    return(0)


def main_mp0():
    """
    main_mp0() to generate a list of left truncatable primes.
    """

    # Printing version info about imported modules.  The other modules do not
    # provide .__version__ info.
    # print('==== multiprocessing module version ' + multiprocessing.__version__ + ' ====')
    numLogicalProcessors = mp.cpu_count()

    # The processes might update milestone_increment and next_milestone, so they need to be
    # multiprocessing shared objects among processes.
    milestone_increment = mp.Value('i', INIT_MILESTONE_INCREMENT)
    next_milestone = mp.Value('i', INIT_MILESTONE_INCREMENT)
    
    # The list foundLeftTruncatables starts with all the single-digit primes,
    # and they happen to be left-truncatable primes as well.
    
    # We are using Queue class from multiprocessing as described in
    # https://docs.python.org/3.5/library/multiprocessing.html

    leftTruncatableSeedsQueue = mp.Queue()
    threadPool = mp.Manager().list()
    foundLeftTruncatables = mp.Manager().list()
    foundLeftTruncatables.append(2)
    foundLeftTruncatables.append(3)
    foundLeftTruncatables.append(5)
    foundLeftTruncatables.append(7)
    # foundLeftTruncatables is started with [2, 3, 5, 7]

    # There is no way to generate new foundLeftTruncatables by prepending digits
    # to 2 and 5.  This implies is_prime(x) does not need to test divisibility
    # against 2 and 5, and we start with 3 and 7.
    leftTruncatableSeedsQueue.put(3)
    leftTruncatableSeedsQueue.put(7)

    # We will start one mp.Process().  It is supposed to generate more left truncatable
    # prime candidates and spawns as many processes (not exceeding numLogicalProcessors)
    # as necessary.
    start_time = time.time()

    # We exit the while loop when len(threadPool) is 0 (no process actively running) and
    # leftTruncatableSeedsQueue is empty.  In theory we should be able to test only
    # len(threadPool).
    while len(threadPool) or not leftTruncatableSeedsQueue.empty():
        # The while loop greedily spawns processes to process candidates from leftTruncatableSeedsQueue
        # until the number of processes hit numLogicalProcessors.
        while len(threadPool) < numLogicalProcessors:
            queueLock.acquire()
            try:
                left_truncatable_candidate = leftTruncatableSeedsQueue.get_nowait()
            except:
                # We did not successfully grab the next candidate from leftTruncatableSeedsQueue,
                # likely it is empty and we will check back later.  We cannot break from while loop
                # here because we will skip over gueueLock.release().
                left_truncatable_candidate = None
            queueLock.release()

            if left_truncatable_candidate:
                # Spawn new mp.Process() to work on left_truncatable_candidate.
                proc = mp.Process(target=process_cand,
                                  args=(left_truncatable_candidate, leftTruncatableSeedsQueue,
                                        foundLeftTruncatables, threadPool,
                                        milestone_increment, next_milestone))
                proc.start()
            else:
                # We can afford spawning new processes, but we are out of candidates to try,
                # so break out of the inner while loop.
                break

        time.sleep(SLEEP_WAITING_TIME)
        
    elapsed_time = time.time() - start_time

    # Now sort the left_truncatable list before printing.
    result_list = foundLeftTruncatables
    result_list.sort()

    # Printing some information.
    print('\nWe found %d left-truncatable primes so far in %0.4f seconds.' \
          % (len(result_list), elapsed_time))
    print("The largest left-truncatable primes are:")
    for left_truncatable in result_list[-NUM_LAST_LEFTTRNCPRIMES_TO_PRINT:]:
        print(left_truncatable)
    return(0)


def main_mp1():
    """
    main_mp1() to generate a list of left truncatable primes.
    """

    # Printing version info about imported modules.  The other modules do not
    # provide .__version__ info.
    # print('==== multiprocessing module version ' + multiprocessing.__version__ + ' ====')
    numLogicalProcessors = mp.cpu_count()

    # The processes might update milestone_increment and next_milestone, so they need to be
    # multiprocessing shared objects among processes.
    milestone_increment = mp.Value('i', INIT_MILESTONE_INCREMENT)
    next_milestone = mp.Value('i', INIT_MILESTONE_INCREMENT)
    
    # The list foundLeftTruncatables starts with all the single-digit primes,
    # and they happen to be left-truncatable primes as well.
    
    procBusy = mp.Manager().list()
    for i in range(numLogicalProcessors):
        procBusy.append(False)
    foundLeftTruncatables = mp.Manager().list()
    foundLeftTruncatables.append(2)
    foundLeftTruncatables.append(3)
    foundLeftTruncatables.append(5)
    foundLeftTruncatables.append(7)
    # foundLeftTruncatables is started with [2, 3, 5, 7]

    # We are using Queue class from multiprocessing as described in
    # https://docs.python.org/3.5/library/multiprocessing.html

    # There is no way to generate new foundLeftTruncatables by prepending digits
    # to 2 and 5.  This implies is_prime(x) does not need to test divisibility
    # against 2 and 5, and we start with 3 and 7.
    leftTruncatableSeedsQueue = mp.Queue()
    leftTruncatableSeedsQueue.put(3)
    leftTruncatableSeedsQueue.put(7)

    # We will start one mp.Process().  It is supposed to generate more left truncatable
    # prime candidates and spawns as many processes (not exceeding numLogicalProcessors)
    # as necessary.
    start_time = time.time()

    # Starting the processes.
    procs = []
    for i in range(numLogicalProcessors):
        p = mp.Process(target=process_cand1,
                       args=(i, leftTruncatableSeedsQueue, foundLeftTruncatables,
                             procBusy, milestone_increment, next_milestone))
        procs.append(p)

    # Starting the processes.
    for p in procs:
        p.start()
        
    # Exit the completed processes:
    for p in procs:
        p.join()

    elapsed_time = time.time() - start_time

    # Now sort the left_truncatable list before printing.
    foundLeftTruncatables.sort()

    # Printing some information.
    print('\nWe found %d left-truncatable primes so far in %0.4f seconds.' \
          % (len(foundLeftTruncatables), elapsed_time))
    print("The largest left-truncatable primes are:")
    for left_truncatable in foundLeftTruncatables[-NUM_LAST_LEFTTRNCPRIMES_TO_PRINT:]:
        print(left_truncatable)
    return(0)


if __name__ == '__main__':
    # Calling main_threading() to use the threading module.
    # main_threading()

    # Calling main_mp0() to use the first implementation with multiprocessing module.
    # main_mp0()

    # Calling main_mp1() to use the second implementation with multiprocessing module.
    main_mp1()
    
