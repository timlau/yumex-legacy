#!/usr/bin/python -E

from subprocess import call
import sys
from yumexbackend import unpack
exit_code = 0

def parse_command(cmd, param):
    if cmd == "#run":
        parameters = unpack(param)
        write(":debug\tLAUNCHER - Starting : %s" % parameters)
        rc = run(parameters)
    elif cmd == "#testrun":
        write(":debug\ttest running : %s" % param)
        run(param)
        rc = True
    elif cmd == "#exit":
        rc = False
    else:
        write(":error\tunknown launcher command : %s" % cmd)
        rc = False
    return rc


def dispatcher():
    write(":debug\tLAUNCHER: Ready for commands")
    write('#ready')
    try:
        line = sys.stdin.readline().strip('\n')
        if not line or line.startswith('#exit'):
            return False
        cmd, param = line.split('\t',2) # Dont blow up if more than 2 x \t instring
        rc = parse_command(cmd, param)
    except IOError, e:
        write(":error\tFatal error in backend launcher (can't read from sys.stdin)")
        write(":error\texception : %s %s " % ("", str(e)))
        rc = False
    except:
        write(":error\tFatal error in backend launcher")
        err, msg = (e.err, e.msg)
        write(":error\texception : %s %s " % (err, msg))
        rc = False
    return rc

def write(msg):
    ''' make a safe writer, the dont blow up if sys.stdout is broken'''
    try:
        print >> sys.stdout, msg
    except:
        sys.exit(5)
    
def run(parameters):
    try:
        global exit_code
        retcode = call(parameters, shell=True)
        exit_code = retcode
        write(":exitcode\t"+str(retcode))
        if retcode == 0: # Normal exit keep launcher running
            rc = True
        else: # abnormal exit, quit the launcher
            rc = False
    except SystemExit, e: # triggered if sys.exit(x) is called
        sys.exit(e)            
    except BaseException,e:
        write(":error\texception : %s %s " % (str(e), str(e.args)))
        rc = False
    return rc

if __name__ == "__main__":
    loop = True
    write("#started")
    while loop:
        loop = False
        rc = dispatcher()
        loop = rc
    write(":debug\tLAUNCHER : Terminating")
    write('&exit')
    sys.exit(exit_code)
