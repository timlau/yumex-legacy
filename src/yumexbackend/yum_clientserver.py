 #!/usr/bin/python -tt
# -*- coding: iso-8859-1 -*-
#    Yum Exteder (yumex) - A GUI for yum
#    Copyright (C) 2008 Tim Lauridsen < tim<AT>yum-extender<DOT>org >
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

# Constants

import sys
import yum
import traceback
import pickle
import base64
import pexpect

class YumPackage:
    ''' Simple object to store yum package information '''
    def __init__(self,base,args):
        self.base = base
        self.name   = args[0]
        self.epoch  = args[1]
        self.ver    = args[2]
        self.rel    = args[3]
        self.arch   = args[4]
        self.repoid = args[5]
        self.summary= args[6]
        
    def __str__(self):
        if self.epoch == '0':
            return '%s-%s-%s.%s' % (self.name,self.ver,self.rel,self.arch)
        else:
            return '%s:%s-%s-%s.%s' % (self.epoch,self.name,self.ver,self.rel,self.arch)

    @property        
    def id(self):        
        return '%s\t%s\t%s\t%s\t%s\t%s' % (self.name,self.epoch,self.ver,self.rel,self.arch,self.repoid)

    def get_attribute(self,attr):
        return self.base.get_attribute(self.id,attr)
    
class YumClient:
    """ Client part of a the yum client/server """

    def __init__(self):
        pass

    def error(self,msg):
        """ error message """
        print "Error:", msg

    def warning(self,msg):
        """ warning message """
        print "Warning:", msg

    def info(self,msg):
        """ info message """
        print "Info:", msg
    
    def debug(self,msg):
        """ debug message """
        print "Debug:", msg

    def action(self,msg):
        """ action message """
        print "Action:", msg

    def exception(self,msg):
        """ debug message """
        print "Exception:", msg

    def timeout(self):
        """ 
        timeout function call every time an timeout occours
        An timeout occaurs if the server takes more then timeout
        periode to respond to the current action.
        the default timeout is .5 sec.
        """
        print "TIMEOUT"

    def setup(self,timeout=.5):
        ''' Setup the client and spawn the server'''
        self.child = pexpect.spawn('./yum_server.py',timeout=timeout)
        self.child.setecho(False)

    def reset(self):
        """ reset the client"""
        self._close()

    def _send_command(self,cmd,args):
        """ send a command to the spawned server """
        line = "%s\t%s" % (cmd,"\t".join(args))
        self.child.expect(':ready')        
        self.child.sendline(line)

    def _parse_command(self,line):
        ''' split command and args for a command received from the server'''
        if line.startswith(':'):
            parts = line.split('\t')
            cmd = parts[0]
            if len(parts) > 1:
                args = parts[1:]
            else:
                args = []
            return cmd,args
        else:
            return None,line
    
    def _readline(self):
        ''' read a line from the server'''
        line = None
        while True:
            try:
                line = self.child.readline()
                break
            except pexpect.TIMEOUT,e:
                self.timeout()
                continue
        return line
            
        
        
    def _check_for_message(self,cmd,args):
        ''' 
        check if the command is a message and call the
        message handler if it is
         '''
        if cmd == ':error':
            self.error(args[0])    
        elif cmd == ':info':
            self.info(args[0])    
        elif cmd == ':debug':
            self.debug(args[0])    
        elif cmd == ':warning':
            self.warning(args[0])
        elif cmd == ':action':
            self.action(args[0])
        elif cmd == ':exception':
            self.exception(args[0])
        else:
            return False # not a message
        return True    
        
    def _get_list(self):
        ''' 
        read a list of :pkg commands from the server, until and
        :end command is received
        '''
        pkgs = []
        cnt = 0L
        while True:
            line = self._readline()
            if line.startswith(':end'):
                break
            cmd,args = self._parse_command(line)
            if cmd:
                if not self._check_for_message(cmd, args):
                    if cmd == ':pkg':
                        p = YumPackage(self,args)
                        pkgs.append(p)
        return pkgs

    def _get_result(self,result_cmd):
        '''
        read a given result command from the server.
        '''
        cnt = 0L
        while True:
            line = self._readline()
            cmd,args = self._parse_command(line)
            if cmd:
                if not self._check_for_message(cmd, args):
                    if cmd == result_cmd:
                        return args
                    else:
                        self.warning("unexpected command : %s (%s)" % (cmd,args))
    
    def _close(self):        
        ''' terminate the child server process '''
        self.child.close(force=True)
        
    def get_packages(self,pkg_filter):    
        ''' get a list of packages based on pkg_filter '''
        self._send_command('get-packages',[str(pkg_filter)])
        pkgs = self._get_list()
        return pkgs

    def get_attribute(self,id,attr):    
        ''' get an attribute of an package '''
        self._send_command('get-attribute',[id,attr])
        args = self._get_result(':attr')
        if args:
            return pickle.loads(base64.b64decode(args[0]))
        else:
            return None
        
    def add_transaction(self,id,action):
        self._send_command('add-transaction',[id,action])
        
    def remove_transaction(self,id,action):
        self._send_command('add-transaction',[id])

    def list_transaction(self):        
        self._send_command('get-transaction',[])

    def run_transaction(self):        
        self._send_command('run-transaction',[])

class YumServer(yum.YumBase):
    """ 
    A yum server class to be used in a spawned process.
    it receives commands from stdin and send results and info
    to stdout.
    
    Commands: (commands and parameters are separated with '\t' )
        get-packages <pkg-filter>            : get a list of packages based on a filter
        get-attribute <pkg_id> <attribute>   : get an attribute of an package
        add-transaction <pkg_id> <action>    : add a po to the transaction
        remove-transaction <pkg_id>          : add a po to the transaction
        list-transaction                     : list po's in transaction
        run-transaction                      : run the transaction
    
        Parameters:
        <pkg-filter> : all,installed,available,updates,obsoletes
        <pkg_id>     : name epoch ver release arch repoid ('\t' separated)
        <attribute>  : pkg attribute (ex. description, changelog)
        <action>     : 'install', 'update', 'remove' 
         
    Results:(starts with and ':' and cmd and parameters are separated with '\t')
    
        :info <message>        : information message
        :action <message>      : action message
        :error <message>       : error message
        :warning <message>     : warning message
        :debug <message>       : debug message
        :exception <message>   : exception message
        :pkg <pkg>             : package
        :end                   : end of package list command
        :attr <object>         : package object attribute
        
        Parameters:
        <message>  : a text message ('\n' is replaced with ';'
        <pkg>      : name epoch ver release arch repoid summary ('\t' separated)
        <object>   : an package attribute pickled and base64 encoded.
      
    
    """
    
    def __init__(self):
        '''  Setup the spawned server '''
        yum.YumBase.__init__(self)
        self.doConfigSetup(errorlevel=0,debuglevel=0)

    def write(self,msg):
        ''' write an message to stdout, to be read by the client'''
        msg.replace("\n",";")
        sys.stdout.write("%s\n" % msg)    
    
    def _show_package(self,pkg):
        ''' write package result'''
        self.write(":pkg\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (pkg.name,pkg.epoch,pkg.ver,pkg.rel,pkg.arch,pkg.repoid,pkg.summary))
    
    def info(self,msg):
        ''' write an info message '''
        self.write(":info\t%s" % msg)

    def error(self,msg):
        ''' write an error message '''
        self.write(":error\t%s" % msg)

    def debug(self,msg):
        ''' write an debug message '''
        self.write(":debug\t%s" % msg)
    
    def warning(self,msg):
        ''' write an warning message '''
        self.write(":warning\t%s" % msg)

    def action(self,msg):
        ''' write an action message '''
        self.write(":action\t%s" % msg)

    def get_packages(self,pkg_narrow):
        ''' get list of packages and send results '''
        if pkg_narrow:
            narrow = pkg_narrow[0]
            ygh = self.doPackageLists(pkgnarrow=narrow)
            for pkg in getattr(ygh,narrow):
                self._show_package(pkg)
        self.write(':end')
        
    def _getPackage(self,para):
        ''' find the real package from an package id'''
        n,e,v,r,a,id = para
        if id == 'installed':
            pkgs = self.rpmdb.searchNevra(n,e,v,r,a)
        else:
            pkgs = self.pkgSack.searchNevra(n,e,v,r,a)
        if pkgs:
            return pkgs[0]
        else:
            return None
        
    def get_attribute(self,args):
        ''' get a package attribute and send the result '''
        pkgstr = args[:-1]
        attr = args[-1]
        po = self._getPackage(pkgstr)
        res = 'none'
        if po:
            if hasattr(po, attr):
                res = getattr(po, attr)
                res = base64.b64encode(pickle.dumps(res))
        self.write(':attr\t%s' % res)
        
    def add_transaction(self,args):
        pkgstr = args[:-1]
        action = args[-1]
        po = self._getPackage(pkgstr)
        txmbrs = []
        if action == "install":
            txmbrs = self.install(po)
        elif action == "update":
            txmbrs = self.update(po)
        elif action == "remove":
            txmbrs = self.remove(po)
        for txmbr in txmbrs:
            self.debug(str(txmbr))            

    def remove_transaction(self,args):
        pkgstr = args
        po = self._getPackage(pkgstr)
        self.tsInfo.remove(po)

    def list_transaction(self):
        for txmbr in self.tsInfo:
            self._show_package(txmbr.po)
            
    def run_transaction(self):
        pass

    def parse_command(self, cmd, args):
        ''' parse the incomming commands and do the actions '''
        if cmd == 'get-packages':
            self.get_packages(args)
        elif cmd == 'get-attribute':
            self.get_attribute(args)
        elif cmd == 'add-transaction':
            self.add_transaction(args)
        elif cmd == 'remove-transaction':
            self.remove_transaction(args)
        elif cmd == 'list-transaction':
            self.list_transaction()
        elif cmd == 'run-transaction':
            self.run_transaction(args)
        else:
            self.error('Unknown command : %s' % cmd)

    def dispatcher(self):
        ''' receive commands and parameter from stdin (from the client) '''        
        try:
            while True:
                self.write(':ready')
                line = sys.stdin.readline().strip('\n')
                if not line or line == 'exit':
                    break
                args = line.split('\t')
                self.parse_command(args[0], args[1:])
        except:
            etype = sys.exc_info()[0]
            evalue = sys.exc_info()[1]
            etb = traceback.extract_tb(sys.exc_info()[2])
            errmsg = 'Error Type: %s ;' % str(etype)
            errmsg += 'Error Value: %s ;' % str(evalue)
            for tub in etb:
                f,l,m,c = tub # file,lineno, function, codeline
                errmsg += '  File : %s , line %s, in %s;' % (f,str(l),m)
                errmsg += '    %s ;' % c
            self.write(":exception\t%s" % errmsg)
            self.write(':end')
        sys.exit(1)

if __name__ == "__main__":
    pass

