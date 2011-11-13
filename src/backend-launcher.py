#!/usr/bin/python -E

from subprocess import call
import sys
from yumexbackend import  pack, unpack


def parse_command(cmd, param):
    if cmd == "#run":
        parameters = unpack(param)
        print ":debug\tLAUNCHER - Starting : %s" % parameters
        rc = run(parameters)
    elif cmd == "#testrun":
        print ":debug\ttest running : %s" % param
        run(param)
        rc = True
    elif cmd == "#exit":
        rc = False
    else:
        print ":error\tunknown launcher command : %s" % cmd
        rc = False
    return rc


def dispatcher():
    print ":debug\tLAUNCHER: Ready for commands"
    print '#ready'
    try:
        line = sys.stdin.readline().strip('\n')
        if not line or line.startswith('#exit'):
            return False
        cmd, param = line.split('\t')
        rc = parse_command(cmd, param)
    except IOError, e:
        print ":error\tFatal error in backend launcher (can't read from sys.stdin)"
        err, msg = (e.err, e.msg)
        print ":error\texception : %s %s " % (err, msg)
        rc = False
    return rc
        
def run(parameters):
    try:
        retcode = call(parameters, shell=True)
        rc = True
    except OSError, e:
        err, msg = (e.err, e.msg)
        print ":error\texception : %s %s " % (err, msg)
        rc = False
    return rc

if __name__ == "__main__":
    loop = True
    print "#started"
    while loop:
        loop = False
        rc = dispatcher()
        loop = rc
    print ":debug\tLAUNCHER : Terminating"
    print '&exit'
