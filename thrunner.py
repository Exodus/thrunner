#!/usr/bin/env python
import argparse
import shlex
import Queue
import re
import smtplib
from os import path
from threading import Thread
from subprocess import Popen, PIPE

#Global Initiators
hostq = Queue.Queue()
logq = Queue.Queue()
log = []
emailregex = r"(^[a-zA-Z0-9_.+-]+@wellsfargo.com$)"

#Create the argument parser for options
parser = argparse.ArgumentParser(description='Create threads for work on multiple servers')
parser.add_argument('serverlist', type=file, help='File with the list of servers')
parser.add_argument('params', help='quoted string with variable %%var%% to replace with host')
parser.add_argument('-t', '--threads', type=int, help='Amount of threads to create')
parser.add_argument('-e', '--email', help='Email the output to <email>')
parser.add_argument('-o', '--output', help='Output file for processing')
parser.add_argument('--noout', action='store_true', help='Do not display any output to the shell')

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

# Validate email
if arg.email is not None:
    if re.match(emailregex, arg.email):
        email = arg.email
    else:
        exit('Wrong email address.')

# Getting the hosts from a file
hosts = arg.serverlist.read().split()

# Set the amount of threads based on the list
if arg.threads is None:
    threads = len(hosts) if len(hosts) <= 100 else 100
else:
    threads = arg.threads
print('Threads: {0}'.format(threads))

# Thread running process
def check_cert(i, q):
    """Runs the check script with host"""
    while True:
        # Get a host from the queue
        host = q.get()
        parm = [p.replace('%var%',host) for p in params]
        print('Thread-{0} Processing: {1}'.format(str(i), host))
        pcheck = Popen(parm, shell=False, stdout=PIPE, stderr=PIPE)
        
        pout = pcheck.communicate()[0]
        print('Thread-'+str(i) + 'Processing: Done\n')
        logq.put(pout)
        print('logq size:' + str(logq.qsize()))
        q.task_done()

# Start the worker threads
for i in range(threads):
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

# Print if --noout unused.
if arg.noout is False:
    print(''.join(log))

# Email if -e --email used.
try:
    email
    server = smtplib.SMTP('localhost')
    server.sendmail('app@wellsfargo.com', email, ''.join(log))
except NameError:
    pass
