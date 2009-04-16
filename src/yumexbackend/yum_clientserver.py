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

import os.path
import sys
import yum
import traceback
import pickle
import base64
import logging
from optparse import OptionParser

import pexpect
from yum.packages import YumAvailablePackage
from yum.packageSack import packagesNewestByNameArch
from urlgrabber.progress import BaseMeter

import yum.Errors as Errors
from yumexbase import *
from yumexbase.i18n import _, P_

import yum.logginglevels as logginglevels
from yum.callbacks import *
from yum.rpmtrans import RPMBaseCallback
from yum.packages import YumLocalPackage
from yum.constants import *

logginglevels._added_handlers = True # let yum think, that logging handlers is already added.

# helper funtion to non string pack/unpack parameter to be transfer over the stdout pipe 

def pack(value):
    '''  Pickle and base64 encode an python object'''
    return base64.b64encode(pickle.dumps(value))
    
def unpack(value):
    '''  base64 decode and unpickle an python object'''
    return pickle.loads(base64.b64decode(value))


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
        self.summary= unpack(args[6])
        self.action = unpack(args[7])
        self.size = args[8]
        self.recent = args[9]
        
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

    def __init__(self,timeout=.1):
        self.child = None
        self._timeout_value = timeout
        self._timeout_last = 0
        self._timeout_count = 0
        self.sending = False
        self.waiting = False
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

    def yum_logger(self,msg):
        """ yum logger message """
        print "YUM:", msg

    def yum_state(self,state):
        """ yum state message handler """
        self.debug("YUM-STATE: %s" % state)

    def _yum_rpm(self,value):
        """ yum rpm action progress message """
        (action, package, percent, ts_current, ts_total) = unpack(value)
        self.yum_rpm_progress(action, package, percent, ts_current, ts_total)

    def yum_rpm_progress(self, action, package, percent, ts_current, ts_total):   
        """ yum rpm action progress handler (overload in child class)"""
        msg = '%s: %s %s %% [%s/%s]' % (action, package, percent, ts_current, ts_total) 
        self.debug("YUM-RPM-PROGRESS: %s" % msg)

    def _yum_dnl(self,value):
        """ yum download action progress message """
        (ftype,name,percent) = unpack(value)
        self.yum_dnl_progress(ftype,name,percent)

    def yum_dnl_progress(self,ftype,name,percent):
        """ yum download progress handler (overload in child class) """   
        self.debug("YUM-DNL:%s : %s - %3i %%" % (ftype,name,percent))

    def fatal(self,args):
        """ fatal backend error """
        err = args[0]
        msg = args[1]
        raise YumexBackendFatalError(err,msg)

    def _timeout(self):
        """ 
        timeout function call every time an timeout occours
        An timeout occaurs if the server takes more then timeout
        periode to respond to the current action.
        the default timeout is .1 sec.
        """
        now = time.time()
        if now-self._timeout_last > self._timeout_value:
            self.timeout(self._timeout_count)
            self._timeout_last = now
            self._timeout_count += 1
            return True
        else:
            return False

    def timeout(self,count):
        """ 
        timeout function call every time an timeout occours
        An timeout occaurs if the server takes more then timeout
        periode to respond to the current action.
        the default timeout is .5 sec.
        """
        print "TIMEOUT"

    def setup(self,debuglevel=2,plugins=True):
        ''' Setup the client and spawn the server'''
        if not self.child:
            self.child = pexpect.spawn('./yum_server.py %i %s' % (debuglevel,plugins),timeout=self._timeout_value)
            self.child.setecho(False)
            return self._wait_for_started()

        else:
            return None

    def reset(self):
        """ reset the client"""
        if not self.child or not self.child.isalive():
            return True
        cnt = 0
        while self.waiting and cnt < 5:
            self.debug("Trying to close the yum backend")
            time.sleep(1)
            cnt += 1
        if cnt < 10:
            rc = self._send_command('exit', [])
            if rc:
                cmd,args = self._readline()
                self._close()
                return True
        # The yum backend did not ended nicely               
        self.error("Yum backend did not close nicely in time")
        self._close()
        return False

        
    def _send_command(self,cmd,args):
        """ send a command to the spawned server """
        line = "%s\t%s" % (cmd,"\t".join(args))
        timeouts = 0
        self.sending = True
        while True:
            try:
                cmd,args = self._readline()
                if cmd == ':ready':
                    break
                elif cmd == None:
                    self.sending = False
                    return False
            except pexpect.TIMEOUT,e:
                self._timeout()
                continue
        self.child.sendline(line)
        self.sending = False
        return True

    def _parse_command(self,line):
        ''' split command and args for a command received from the server'''
        line = line.strip()
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
        if self.waiting: # Somebody else is already waiting for something
            return None,None
        while True:
            try:
                self.waiting = True
                if self.child:
                    line = self.child.readline()
                else: # We are closing
                    self.waiting = False
                    return None,None
                cmd,args = self._parse_command(line)
                self._timeout()
                if cmd:
                    if self._check_for_message(cmd, args):
                        continue
                    else:
                        self.waiting = False
                        return cmd,args
            except pexpect.TIMEOUT,e:
                self._timeout()
                continue
            
        
        
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
        elif cmd == ':yum':
            self.yum_logger(args[0])
        elif cmd == ':fatal':
            self.fatal(args)
        elif cmd == ':yum-rpm': # yum rpm action progress
            self._yum_rpm(args[0])
        elif cmd == ':yum-dnl': # yum dnl progress
            self._yum_dnl(args[0])
        elif cmd == ':yum-state':
            self.yum_state(args[0])
        else:
            return False # not a message
        return True    
    
    def _wait_for_started(self):
        cnt = 0
        while True:
            cmd,args = self._readline()
            cnt += 1
            if cmd == ':started':
                return True
            
        
    def _get_list(self,result_cmd=":pkg"):
        ''' 
        read a list of :pkg commands from the server, until and
        :end command is received
        '''
        data = []
        cnt = 0L
        while True:
            cmd,args = self._readline()
            if cmd == ':end':
                break
            if cmd == None: # readline is locked:
                break
            elif not cmd == result_cmd: 
                self.warning("_get_list unexpected command : %s (%s)" % (cmd,args))
            elif cmd == ':pkg':
                p = YumPackage(self,args)
                data.append(p)
            else:
                data.append(args)
        return data

    def _get_result(self,result_cmd):
        '''
        read a given result command from the server.
        '''
        cnt = 0L
        while True:
            cmd,args = self._readline()
            if not self._check_for_message(cmd, args):
                if cmd == result_cmd:
                    return args
                elif cmd == None: # readline is locked
                    break
                else:
                    self.warning("_get_result unexpected command : %s (%s)" % (cmd,args))
    
    def _get_messages(self):
        ''' 
        read a list of :msg commands from the server, until and
        :end command is received
        '''
        msgs = {}
        while True:
            cmd,args = self._readline()
            if cmd == ':end':
                break
            elif cmd == ':msg':
                msg_type = args[0]
                value = unpack(args[1])
                if msg_type in msgs:
                    msgs[msg_type].append(value)
                else:
                    msgs[msg_type] = [value]
        return msgs
            
    
    def _close(self):        
        ''' terminate the child server process '''
        if self.child:
            self.child.close(force=True)
            self.child = None
        
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
            return unpack(args[0])
        else:
            return None
        
    def add_transaction(self,id,action):
        self._send_command('add-transaction',[id,action])
        pkgs = self._get_list()
        return pkgs
        
    def remove_transaction(self,id,action):
        self._send_command('remove-transaction',[id])
        pkgs = self._get_list()
        return pkgs

    def list_transaction(self):        
        self._send_command('list-transaction',[])
        pkgs = self._get_list()
        return pkgs

    def build_transaction(self):        
        self._send_command('build-transaction',[])
        msgs = self._get_messages()
        return msgs['return_code'][0],msgs['messages'],unpack(msgs['transaction'][0])

    def run_transaction(self):        
        self._send_command('run-transaction',[])

    def get_groups(self):
        self._send_command('get-groups',[])

    def get_repos(self):
        self._send_command('get-repos',[])
        data = self._get_list(':repo')
        repos = []
        for state,id,name,gpg in data:
            gpg = gpg == 'True'
            state = state == 'True'
            elem = (state,id,name,gpg)
            repos.append(elem)
        return repos
        
    def enable_repo(self,id,state):
        self._send_command('enable-repo',[id,str(state)])
        args = self._get_result(':repo')
        return args
        
        
    def search(self,keys,filters):
        bKeys = pack(keys)
        bFilters = pack(filters)
        self._send_command('search',[bKeys,bFilters])
        pkgs = self._get_list()
        return pkgs
        
        
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
        build-transaction                    : build the transaction (resolve dependencies)
        run-transaction                      : run the transaction
        get-groups                           : Get the groups
        get-repos                            : Get the repositories
        enable-repo                          : enable/disable a repository
        search                               : search
    
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
        :yum <message>         : yum logger message
        :pkg <pkg>             : package
        :end                   : end of package list command
        :attr <object>         : package object attribute
        :group <grp>           : group
        :repo <repo>           : repo
        :msg <type> <value>
        
        Parameters:
        <message>  : a text message ('\n' is replaced with ';'
        <pkg>      : name epoch ver release arch repoid summary ('\t' separated)
        <object>   : an package attribute pickled and base64 encoded.
      
    
    """
    
    def __init__(self,debuglevel=2,plugins=True):
        '''  Setup the spawned server '''
        yum.YumBase.__init__(self)
        plainformatter = logging.Formatter("%(message)s")    
        self.handler = YumLogHandler(self)
        self.handler.setFormatter(plainformatter)
        self.yum_verbose = logging.getLogger("yum.verbose")
        self.yum_verbose.propagate = False
        self.yum_verbose.addHandler(self.handler)
        self.yum_verbose.setLevel(logginglevels.DEBUG_3)
        
        self.doConfigSetup(debuglevel=debuglevel, plugin_types=( yum.plugins.TYPE_CORE, ),init_plugins=plugins)
        self.doLock()
        self.dnlCallback = YumexDownloadCallback(self)
        self.repos.setProgressBar(self.dnlCallback)
        # make some dummy options,args for yum plugins
        parser = OptionParser()
        ( options, args ) = parser.parse_args()
        self.plugins.setCmdLine(options,args)
        self.write(':started')



    def doLock(self):
        cnt = 0
        while cnt < 5:
            try:
                yum.YumBase.doLock(self)
                return True
            except Errors.LockError, e:
                self.error(e.msg)
                cnt += 1
                time.sleep(2)
        self.fatal("lock-error", e.msg )        
                
    def quit(self):
        self.debug("Closing rpm db and releasing yum lock  ")
        self.closeRpmDB()
        self.doUnlock()
        self.write(':end')
        sys.exit(1)

    def write(self,msg):
        ''' write an message to stdout, to be read by the client'''
        msg.replace("\n",";")
        sys.stdout.write("%s\n" % msg)    
        
    def _get_recent(self,po):
        if po.repoid == 'installed':
            ftime = int( po.returnSimple( 'installtime' ) )
        else:
            ftime = int( po.returnSimple( 'filetime' ) )
        if ftime > RECENT_LIMIT:
            return 1
        else:
            return 0
                    
    
    def _show_package(self,pkg,action=None):
        ''' write package result'''
        summary = pack(pkg.summary)
        recent = self._get_recent(pkg)
        action = pack(action)
        self.write(":pkg\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (pkg.name,pkg.epoch,pkg.ver,pkg.rel,pkg.arch,pkg.repoid,summary,action,pkg.size,recent))
        
    def _show_group(self,grp):
        self.write(":group\t%s\t%s\t%s" % (cat,id,name) )

    def _show_repo(self,repo):
        self.write(":repo\t%s\t%s\t%s\t%s" % (repo.enabled,repo.id,repo.name,repo.gpgcheck) )

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

    def fatal(self,err,msg):
        ''' write an fatal message '''
        self.write(":fatal\t%s\t%s" % (err,msg))
        sys.exit(1)

    def message(self,msg_type,value):
        value = pack(value)
        self.write(":msg\t%s\t%s" % (msg_type,value))

    def yum_rpm(self, action, package, frac, ts_current, ts_total):
        ''' write an yum rpm action progressmessage '''
        value = (action, package, frac, ts_current, ts_total)
        value = pack(value)
        self.write(":yum-rpm\t%s" % value)
        
    def yum_dnl(self,ftype, name, percent):
        value = (ftype,name,percent)
        value = pack(value)
        self.write(":yum-dnl\t%s" % value)
        
    def yum_state(self,state):
        ''' write an yum transaction state message '''
        self.write(":yum-state\t%s" % state)
       
    def yum_logger(self,msg):
        ''' write an yum logger message '''
        self.write(":yum\t%s" % msg)

    def get_packages(self,pkg_narrow):
        ''' get list of packages and send results '''
        if pkg_narrow:
            narrow = pkg_narrow[0]
            action = FILTER_ACTIONS[narrow]
            ygh = self.doPackageLists(pkgnarrow=narrow)
            for pkg in getattr(ygh,narrow):
                self._show_package(pkg,action)
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
        self.debug("Getting attribute : %s from %s " % ( attr,str(po)))
        res = pack(None)
        if po:
            res = getattr(po, attr)
            self.debug("Attribute : %s : len = %i " % ( attr,len(res)))
            res = pack(res)
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
            self._show_package(txmbr.po,txmbr.ts_state)
            self.debug("Added : "+ str(txmbr))            
        self.write(':end')
            
    def remove_transaction(self,args):
        pkgstr = args
        po = self._getPackage(pkgstr)
        self.tsInfo.remove(po)

    def list_transaction(self):
        for txmbr in self.tsInfo:
            self._show_package(txmbr.po,txmbr.ts_state)
        self.write(':end')
            
    def build_transaction(self):
        rc, msgs = self.buildTransaction()
        self.message('return_code', rc)
        for msg in msgs:
            self.message('messages', msg)
        self.message('transaction', pack(self._get_transaction_list()))
        self.write(':end')
        
    def _get_transaction_list( self ):
        list = []
        sublist = []
        self.tsInfo.makelists()        
        for ( action, pkglist ) in [( _( 'Installing' ), self.tsInfo.installed ), 
                            ( _( 'Updating' ), self.tsInfo.updated ), 
                            ( _( 'Removing' ), self.tsInfo.removed ), 
                            ( _( 'Installing for dependencies' ), self.tsInfo.depinstalled ), 
                            ( _( 'Updating for dependencies' ), self.tsInfo.depupdated ), 
                            ( _( 'Removing for dependencies' ), self.tsInfo.depremoved )]:
            for txmbr in pkglist:
                ( n, a, e, v, r ) = txmbr.pkgtup
                evr = txmbr.po.printVer()
                repoid = txmbr.repoid
                pkgsize = float( txmbr.po.size )
                size = format_number( pkgsize )
                alist=[]
                for ( obspo, relationship ) in txmbr.relatedto:
                    if relationship == 'obsoletes':
                        appended = 'replacing  %s.%s %s' % ( obspo.name, 
                            obspo.arch, obspo.printVer() )
                        alist.append( appended )
                el = ( n, a, evr, repoid, size, alist )
                sublist.append( el )
            if pkglist:
                list.append( [action, sublist] )
                sublist = []
        return list        
        
                    
    def run_transaction(self):
        try:
            rpmDisplay = YumexRPMCallback(self)
            callback = YumexTransCallback(self)
            self.processTransaction(callback=callback, rpmDisplay=rpmDisplay)
        except:
            self.error("Exception in run_transaction")
            
    
    def get_groups(self,args):
        pass

    def search(self,args):
        keys = unpack(args[0])
        filters = unpack(args[1])
        ygh = self.doPackageLists(pkgnarrow='updates')
        pkgs = {}
        for found in self.searchGenerator(filters,keys,showdups=True, keys=True):
            pkg = found[0]
            fkeys = found[1]
            if not len(fkeys) == len(keys): # skip the result if not all keys matches
                continue
            na = "%s.%s" % (pkg.name,pkg.arch)
            if not na in pkgs:
                pkgs[na] = [pkg]
            else:
                pkgs[na].append(pkg)
        for na in pkgs:
            best = packagesNewestByNameArch(pkgs[na])
            for po in best:           
                if self.rpmdb.contains(po=po): # if the best po is installed, then return the installed po 
                    (n,a,e,v,r) = po.pkgtup
                    po= self.rpmdb.searchNevra(name=n, arch=a, ver=v, rel=r, epoch=e)[0]
                    action = 'r'
                else:
                    if po in ygh.updates:
                        action = 'u'
                    else:
                        action = 'i'
                self._show_package(po, action)    
        self.write(':end')
    
    def get_repos(self,args):
        for repo in self.repos.repos:
            self._show_repo(self.repos.getRepo(repo))
        self.write(':end')
            
    
    def enable_repo(self,args):
        id = args[0]
        state = (args[1] == 'True')
        self.debug("Repo : %s Enabled : %s" % (id,state))
        repo = self.repos.getRepo(id)
        if repo:
            if state:
                self.repos.enableRepo(id)
            else:
                self.repos.disableRepo(id)
            self._show_repo(repo)
        else:
            self.error("Repo : %s not found" % id)

    def parse_command(self, cmd, args):
        ''' parse the incomming commands and do the actions '''
        self._timeout_count = 0
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
            self.run_transaction()
        elif cmd == 'build-transaction':
            self.build_transaction()
        elif cmd == 'get-groups':
            self.get_groups(args)
        elif cmd == 'get-repos':
            self.get_repos(args)
        elif cmd == 'enable-repo':
            self.enable_repo(args)
        elif cmd == 'search':
            self.search(args)
        else:
            self.error('Unknown command : %s' % cmd)

    def dispatcher(self):
        ''' receive commands and parameter from stdin (from the client) '''        
        try:
            while True:
                self.write(':ready')
                line = sys.stdin.readline().strip('\n')
                if not line or line.startswith('exit'):
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
        self.quit()

class YumexTransCallback:
    def __init__(self, base):
        self.base = base

    def event(self, state, data=None):

        if state == PT_DOWNLOAD:        # Start Downloading
            self.base.yum_state('download')
        elif state == PT_DOWNLOAD_PKGS:   # Packages to download
            self.base.dnlCallback.setPackages(data, 10, 30)
        elif state == PT_GPGCHECK:
            self.base.yum_state('gpg-check')
        elif state == PT_TEST_TRANS:
            self.base.yum_state('test-transaction')
        elif state == PT_TRANSACTION:
            self.base.yum_state('transaction')


class YumexRPMCallback(RPMBaseCallback):
    
    def __init__(self,base):
        RPMBaseCallback.__init__(self)
        self.base = base
        self._last_frac = 0.0
        self._last_pkg = None

    def event(self, package, action, te_current, te_total, ts_current, ts_total):
        # Handle rpm transaction progress
        try:
            if action != TS_UPDATED:
                if self._last_pkg != package:
                    self._last_pkg = package
                    self._last_frac = 0.0
                frac = float(te_current)/float(te_total)
                if frac > self._last_frac + 0.005:
                    #self.base.debug(str([self.action[action], str(package), frac, ts_current, ts_total]))
                    self.base.yum_rpm(self.action[action], str(package), frac, ts_current, ts_total)
                    self._last_frac = frac
            else:
                self.base.yum_rpm(self.action[action], str(package), 1.0, ts_current, ts_total)
                
        except:
            self.base.debug('RPM Callback error : %s - %s ' % (self.action[action], str(package)))
            etype = sys.exc_info()[0]
            self.base.debug(str(etype))
        
    def scriptout(self, package, msgs):
        # Handle rpm scriptlet messages
        if msgs:
            for msg in msgs:
                self.base.debug('RPM : %s' % msg)

class YumexDownloadCallback(DownloadBaseCallback):
    """ Download callback handler """
    def __init__(self,base):
        DownloadBaseCallback.__init__(self)
        self.base = base
        self.percent_start = 0
        self.saved_pkgs = None
        self.number_packages = 0
        self.download_package_number = 0
        self.current_name = None
        self.current_type = None

    def setPackages(self, new_pkgs, percent_start, percent_length):
        self.saved_pkgs = new_pkgs
        self.number_packages = float(len(self.saved_pkgs))
        self.percent_start = percent_start

    def _getPackage(self, name):
        if self.saved_pkgs:
            for pkg in self.saved_pkgs:
                if isinstance(pkg, YumLocalPackage):
                    rpmfn = pkg.localPkg
                else:
                    rpmfn = os.path.basename(pkg.remote_path) # get the rpm filename of the package
                if rpmfn == name:
                    return pkg
        return None
        
    def updateProgress(self, name, frac, fread, ftime):
        '''
         Update the progressbar (Overload in child class)
        @param name: filename
        @param frac: Progress fracment (0 -> 1)
        @param fread: formated string containing BytesRead
        @param ftime: formated string containing remaining or elapsed time
        '''

        val = int(frac*100)

        # new package
        if val == 0:
            if ':' in name:
                c,n = name.split(':')
                name = n.strip()
                cur,tot = c[1:-1].split('/') 
            pkg = self._getPackage(name)
            if pkg: # show package to download
                self.current_name = str(pkg)
                self.current_type = 'PKG'
            elif not name.endswith('.rpm'):
                self.current_name = name
                self.current_type = 'REPO'
            else:
                self.current_name = name
                self.current_type = 'PKG'
                

        self.base.yum_dnl(self.current_type,self.current_name,val)

        # keep track of how many we downloaded
        if val == 100:
            self.download_package_number += 1
            self.current_name = None



class YumLogHandler(logging.Handler):
    ''' Python logging handler for writing in a TextViewConsole'''
    def __init__(self, base):
        logging.Handler.__init__(self)
        self.base = base

    def emit(self, record):   
        msg = self.format(record)
        if self.base:
            self.base.yum_logger(msg)

def setup_logging(base):
    #logging.basicConfig()    
    plainformatter = logging.Formatter("%(message)s")    
    handler = YumLogHandler(base)
    handler.setFormatter(plainformatter)
    verbose = logging.getLogger("yum.verbose")
    verbose.propagate = False
    verbose.addHandler(handler)
    verbose.setLevel(logginglevels.DEBUG_3)
    #verbose.setLevel(logginglevels.INFO_2)
    
if __name__ == "__main__":
    pass

