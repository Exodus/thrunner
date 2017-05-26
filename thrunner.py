#!/usr/bin/env python
# A Python script for running threaded shell executions with variable replacement fed through a file
# Miguel A. Alvarado V.
import argparse
import shlex
from threading import Thread
import Queue
from subprocess import Popen, PIPE

parser = argparse.ArgumentParser(description='Multiple Threads Runner')
parser.add_argument('serverlist', type=file, help='')
parser.add_argument('params', help='Parameters used to exec')
parser.add_argument('-t', '--threads', type=int, help='Amount of threads to spawn')
parser.parse_args()

# Initializing some global objects
threads = parser.threads
params = parser.params
hosts = parser.serverlist.read().split()
hostq = Queue.Queue()
logq = Queue.Queue()
msgs = []



# Worker thread: thread # and queue.
def runner(id, queue):
    while True:
        # Get a host from the queue
        host = queue.get()
        # Prepare the arguments for execution <<missing the host logic>>
        args = shlex.split(params)
        process = Popen(args, shell=False, stdout=PIPE, stderr=PIPE)
        # Put only stdout in the log queue
        logq.put(process.communicate()[0])

# Start the worker threads
for threadid in range(threads):
    worker = Thread(target=runner, args=(threadid, hostq))
    worker.setDaemon = True
    worker.start()

# Fill the queue
for host in hosts:
    hostq.put(host)

# Wait for the worker threads to finish all the tasks
hostq.join()

# Put the logs in a list
while True:
    try:
        msgs.append(logq.get_nowait())
    except Queue.Empty:
        break

# Print the log
for msg in msgs:
    print(msg)