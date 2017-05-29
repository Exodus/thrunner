#!/usr/bin/env python
import argparse
import shlex
import Queue
from os import path
from threading import Thread
from subprocess import Popen, PIPE


#Global Initiators
hostq = Queue.Queue()
logq = Queue.Queue()
log = []

#Create the argument parser for options
parser = argparse.ArgumentParser(description='Create threads for work on multiple servers')
parser.add_argument('serverlist', type=file, help='File with the list of servers')
parser.add_argument('params', help='quoted string with variable %var% to replace with host')
parser.add_argument('-t', '--threads', type=int, default=2, help='Amount of threads to create')
parser.add_argument('-e', '--email', help='Email the output to <email>')
parser.add_argument('-o', '--output', help='Output file for processing')

# Python version argparse issue with a file not found
try:
    arg = parser.parse_args()
except IOError:
    exit('Host file not found')

# Parsing the parameters
params = shlex.split(arg.params)
params[0] = path.abspath(params[0])
if not any('%var%' in param for param in params):
    exit('%var% not present')
if not path.isfile(params[0]):
    exit('Executable file not found')

# Getting the hosts from a file
hosts = arg.serverlist.read().split()

# Thread running process
def check_cert(i, q):
    """Runs the check script with host"""
    while True:
        # Get a host from the queue
        host = q.get()
        parm = [p.replace('%var%',host) for p in params]
        print('Thread-' + str(i) + ' Processing: ' + host + '\n')
        pcheck = Popen(parm, shell=False, stdout=PIPE, stderr=PIPE)
        
        pout = pcheck.communicate()[0]
        print('Thread-'+str(i) + 'Processing: Done\n')
        logq.put(pout)
        print('logq size:' + str(logq.qsize()))
        q.task_done()

# Start the worker threads
for i in range(arg.threads):
    worker = Thread(target=check_cert, args=(i, hostq))
    worker.setDaemon(True)
    worker.start()

# Fill in the queue
for host in hosts:
    hostq.put(host)

hostq.join()


while True:
    try:
        log.append(logq.get_nowait())
    except Queue.Empty:
        break

for entry in log:
    print(entry)
