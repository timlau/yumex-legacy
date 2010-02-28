# need the python-argparse package installed
import argparse

# create the parser
main_parser = None

def setupParser():
    global main_parser
    base_parser = argparse.ArgumentParser(add_help=False)
    parser = base_parser.add_argument_group('base options')
    parser.add_argument("-d", "--debuglevel", dest="debuglevel", action="store", choices=xrange(10),
            default=2, help="yum output level", type=int)      
    parser.add_argument("-e","--errorlevel", dest="errorlevel", action="store", choices=xrange(10),
            default=2, help="yum error level", type=int)      
    main_parser = argparse.ArgumentParser(description='GUI for the yum package manager', parents = [base_parser])
    subparsers = main_parser.add_subparsers()
    
    cmds = ['install','remove']
    # add a sub-command "install"
    for c in cmds:
        parser_cmd = subparsers.add_parser(c, help='%s a package' % c, parents = [base_parser])
        parser_cmd.add_argument('package', nargs='*')
    

if __name__ == '__main__':
    
    setupParser()
    # parse the command line
    args = main_parser.parse_args()
    print args

