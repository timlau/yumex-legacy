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

'''
'''

import sys
import pickle
import base64
import os

import pexpect

from yumexbase.constants import *
from yumexbase import YumexBackendFatalError

# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
import logging
from yumexbase.i18n import _, P_
# pylint: enable-msg=W0611


#logginglevels._added_handlers = True # let yum think, that logging handlers is already added.

# helper funtion to non string pack/unpack parameter to be transfer over the stdout pipe 
def pack(value):
    '''  Pickle and base64 encode an python object'''
    return base64.b64encode(pickle.dumps(value))
    
def unpack(value):
    '''  base64 decode and unpickle an python object'''
    return pickle.loads(base64.b64decode(value))


class YumPackage:
    ''' Simple object to store yum package information '''
    def __init__(self, base, args):
        '''
        
        @param base:
        @param args:
        '''
        self.base = base
        self.name = args[0]
        self.epoch = args[1]
        self.ver = args[2]
        self.rel = args[3]
        self.arch = args[4]
        self.repoid = args[5]
        self.summary = unpack(args[6])
        self.action = unpack(args[7])
        self.size = args[8]
        self.recent = args[9]

    def __str__(self):
        '''
        string representation of the package object
        '''
        return self.fullname
        
    @property
    def fullname(self):
        ''' Package fullname  '''        
        if self.epoch and self.epoch <> '0':
            return "%s-%s:%s.%s.%s" % (self.name, self.epoch, self.ver, self.rel, self.arch)
        else:   
            return "%s-%s.%s.%s" % (self.name, self.ver, self.rel, self.arch)

    @property        
    def id(self):        
        '''
        
        '''
        return '%s\t%s\t%s\t%s\t%s\t%s' % (self.name, self.epoch, self.ver, self.rel, self.arch, self.repoid)

    def get_attribute(self, attr):
        '''
        
        @param attr:
        '''
        return self.base.get_attribute(self.id, attr)
    
    def get_changelog(self, num):
        '''
        
        @param num:
        '''
        return self.base.get_changelog(self.id, num)
    
    def get_update_info(self):
        return self.base.get_update_info(self.id)
    
class YumClient:
    """ Client part of a the yum client/server """

    def __init__(self, timeout = .1):
        '''
        
        @param timeout:
        '''
        self.child = None
        self._timeout_value = timeout
        self._timeout_last = 0
        self._timeout_count = 0
        self.sending = False
        self.waiting = False
        self.end_state = None

    def error(self, msg):
        """ error message (overload in child class)"""
        raise NotImplementedError()

    def warning(self, msg):
        """ warning message (overload in child class)"""
        raise NotImplementedError()

    def info(self, msg):
        """ info message (overload in child class)"""
        raise NotImplementedError()
    
    def debug(self, msg):
        """ debug message (overload in child class)"""
        raise NotImplementedError()

    def exception(self, msg):
        """ debug message (overload in child class)"""
        raise NotImplementedError()

    def yum_logger(self, msg):
        """ yum logger message (overload in child class)"""
        raise NotImplementedError()

    def yum_state(self, state):
        """ yum state message handler (overload in child class)"""
        raise NotImplementedError()

    def _yum_rpm(self, value):
        """ yum rpm action progress message """
        (action, package, percent, ts_current, ts_total) = unpack(value)
        self.yum_rpm_progress(action, package, percent, ts_current, ts_total)

    def yum_rpm_progress(self, action, package, percent, ts_current, ts_total):   
        """ yum rpm action progress handler (overload in child class)"""
        raise NotImplementedError()

    def _yum_dnl(self, value):
        """ yum download action progress message """
        (ftype, name, percent, cur, tot, fread, ftotal, ftime) = unpack(value)
        self.yum_dnl_progress(ftype, name, percent, cur, tot, fread, ftotal, ftime)

    def yum_dnl_progress(self, ftype, name, percent, cur, tot, fread, ftotal, ftime):
        """ yum download progress handler (overload in child class) """   
        raise NotImplementedError()

    def _gpg_check(self, value):
        """ yum download action progress message """
        (po, userid, hexkeyid) = unpack(value)
        ok = self.gpg_check(po, userid, hexkeyid)
        if ok:
            self.child.sendline(":true")
        else:
            self.child.sendline(":false")
            
    def gpg_check(self, po, userid, hexkeyid):
        """  Confirm GPG key (overload in child class) """
        return False
    
    def _media_change(self, value):
        """ media change signal """
        (prompt_first, media_id, media_name, media_num) = unpack(value)
        mp = self.media_change(prompt_first, media_id, media_name, media_num)
        self.child.sendline(":mountpoint\t%s" % pack(mp))
            
    def media_change(self, prompt_first, media_id, media_name, media_num):
        """  media change (overload in child class) """
        return False

    def fatal(self, args):
        """ fatal backend error """
        err = args[0]
        msg = unpack(args[1])
        raise YumexBackendFatalError(err, msg)

    def _timeout(self):
        """ 
        timeout function call every time an timeout occours
        An timeout occaurs if the server takes more then timeout
        periode to respond to the current action.
        the default timeout is .1 sec.
        """
        now = time.time()
        if now - self._timeout_last > self._timeout_value:
            self.timeout(self._timeout_count)
            self._timeout_last = now
            self._timeout_count += 1
            return True
        else:
            return False

    def timeout(self, count):
        """ 
        timeout child handler, called from the main timeout handler
        An timeout occaurs if the server takes more then timeout
        periode to respond to the current action.
        the default timeout is .1 sec.
        """
        raise NotImplementedError()

    def setup(self, debuglevel = 2, plugins = True, filelog = False, offline = False, repos = None, proxy = None):
        ''' Setup the client and spawn the server'''
        if not self.child:
            prefix = ""
            args = []
            if MAIN_PATH == '/usr/share/yumex': # Non root
                cmd = '/usr/bin/yumex-yum-backend'
            else:
                self.info('Running backend with sudo (%s)' % (MAIN_PATH + "/yum_childtask.py"))
                cmd ='/usr/bin/sudo' 
                args.append(MAIN_PATH + "/yum_childtask.py")
            args.append(str(debuglevel)) # debuglevel
            args.append(str(plugins))    # plugins 
            args.append(str(offline))    # is offline
            if repos:                    # enabled repos
                repo_str = ";".join(repos)
                args.append(repo_str)
#            if proxy:
#                prefix="HTTP_PROXY=%s " % proxy
#                self.info("Setting : %s" % prefix)
            self.child = pexpect.spawn(cmd,args, timeout = self._timeout_value)
            self.child.setecho(False)
            if filelog:
                self.child.logfile_read = sys.stdout
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
                cmd, args = self._readline()
                self._close()
                return True
        # The yum backend did not ended nicely               
        self.error("Yum backend did not close nicely in time")
        self._close()
        return False

        
    def _send_command(self, cmd, args):
        """ send a command to the spawned server """
        line = "%s\t%s" % (cmd, "\t".join(args))
        self.debug('Sending command: %s args: %s' % (cmd, str(args)))
        timeouts = 0
        self.sending = True
        self.end_state = None        
        while True:
            try:
                cmd, args = self._readline()
                if cmd == ':ready':
                    break
                elif cmd == None:
                    self.sending = False
                    return False
            except pexpect.TIMEOUT, e:
                self._timeout()
                continue
        self.child.sendline(line)
        self.sending = False
        return True

    def _parse_command(self, line):
        ''' split command and args for a command received from the server'''
        line = line.strip()
        if line.startswith(':'):
            parts = line.split('\t')
            cmd = parts[0]
            if len(parts) > 1:
                args = parts[1:]
            else:
                args = []
            return cmd, args
        else:
            return None, line
    
    def _readline(self):
        ''' read a line from the server'''
        line = None
        if self.waiting: # Somebody else is already waiting for something
            return None, None
        while True:
            try:
                self.waiting = True
                if self.child:
                    line = self.child.readline()
                else: # We are closing
                    self.waiting = False
                    return None, None
                cmd, args = self._parse_command(line)
                self._timeout()
                if cmd:
                    if self._check_for_message(cmd, args):
                        continue
                    else:
                        self.waiting = False
                        return cmd, args
                else:
                    self.yum_logger(line.strip('\n'))
            except pexpect.TIMEOUT, e:
                self._timeout()
                continue
            
    def _check_for_message(self, cmd, args):
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
        elif cmd == ':exception':
            self.exception(args[0])
        elif cmd == ':yum':
            self.yum_logger(args[0])
        elif cmd == ':fatal':
            self.fatal(args)
        elif cmd == ':gpg-check':
            self._gpg_check(args[0])
        elif cmd == ':media-change':
            self._media_change(args[0])
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
        '''
        
        '''
        cnt = 0
        while True:
            cmd, args = self._readline()
            cnt += 1
            if cmd == ':started':
                return True
            
    def is_ended(self, cmd, args):
        '''
        
        @param cmd:
        @param args:
        '''
        if cmd == ':end':
            if args:
                self.end_state = unpack(args[0])
            else: # no parameter to :end
                self.end_state = True
            return True
        else:
            return False
        
    def _get_list(self, result_cmd = ":pkg"):
        ''' 
        read a list of :pkg commands from the server, until and
        :end command is received
        '''
        data = []
        cnt = 0L
        while True:
            cmd, args = self._readline()
            if self.is_ended(cmd, args):
                break
            if cmd == None: # readline is locked:
                break
            elif not cmd == result_cmd: 
                self.warning("_get_list unexpected command : %s (%s)" % (cmd, args))
            elif cmd == ':pkg':
                po = YumPackage(self, args)
                data.append(po)
            else:
                data.append(args)
        return data

    def _get_result(self, result_cmd):
        '''
        read a given result command from the server.
        '''
        cnt = 0L
        while True:
            cmd, args = self._readline()
            if not self._check_for_message(cmd, args):
                if cmd == result_cmd:
                    return args
                elif cmd == None: # readline is locked
                    break
                else:
                    self.warning("_get_result unexpected command : %s (%s)" % (cmd, args))
    
    def _get_messages(self):
        ''' 
        read a list of :msg commands from the server, until and
        :end command is received
        '''
        msgs = {}
        while True:
            cmd, args = self._readline()
            if self.is_ended(cmd, args):
                break
            elif cmd == ':msg':
                msg_type = args[0]
                value = unpack(args[1])
                if msg_type in msgs:
                    msgs[msg_type].append(value)
                else:
                    msgs[msg_type] = [value]
        return msgs
            
    def _get_return_code(self):
        while True:
            cmd, args = self._readline()
            if self.is_ended(cmd, args):
                break
        return self.end_state
    
    def _close(self):        
        ''' terminate the child server process '''
        if self.child:
            self.child.close(force = True)
            self.child = None
        
    def get_packages(self, pkg_filter):    
        ''' get a list of packages based on pkg_filter '''
        self._send_command('get-packages', [str(pkg_filter)])
        pkgs = self._get_list()
        return pkgs

    def get_packages_size(self, ndx):    
        ''' get a list of packages based on pkg_filter '''
        self._send_command('get-packages-size', [str(ndx)])
        pkgs = self._get_list()
        return pkgs

    def set_option(self, option, value, on_repos = False):    
        ''' get a list of packages based on pkg_filter '''
        self._send_command('set-option', [option,pack(value),pack(on_repos)])
        return self._get_return_code()

    def get_attribute(self, ident, attr):    
        ''' get an attribute of an package '''
        self._send_command('get-attribute', [ident, attr])
        args = self._get_result(':attr')
        if args:
            return unpack(args[0])
        else:
            return None

    def get_changelog(self, ident, num):    
        ''' get an attribute of an package '''
        self._send_command('get-changelog', [ident, str(num)])
        args = self._get_result(':attr')
        if args:
            return unpack(args[0])
        else:
            return None

    def get_update_info(self,ident):  
        self._send_command('update-info', [ident])
        msgs = self._get_messages()
        return msgs['updateinfo'][0]
              
    def add_transaction(self, ident, action):
        '''
        
        @param ident:
        @param action:
        '''
        self._send_command('add-transaction', [ident, action])
        pkgs = self._get_list()
        return pkgs
        
    def remove_transaction(self, ident, action):
        '''
        
        @param ident:
        @param action:
        '''
        self._send_command('remove-transaction', [ident])
        pkgs = self._get_list()
        return pkgs

    def list_transaction(self):        
        '''
        
        '''
        self._send_command('list-transaction', [])
        pkgs = self._get_list()
        return pkgs

    def reset_transaction(self):        
        '''
        
        '''
        self._send_command('reset-transaction', [])

    def build_transaction(self):        
        '''
        
        '''
        self._send_command('build-transaction', [])
        msgs = self._get_messages()
        return msgs['return_code'][0], msgs['messages'], unpack(msgs['transaction'][0])

    def run_transaction(self):        
        '''
        
        '''
        self._send_command('run-transaction', [])
        lst = self._get_list()
        return self.end_state

    def get_groups(self):
        '''
        
        '''
        self._send_command('get-groups', [])
        msgs = self._get_messages()
        return unpack(msgs['groups'][0])

    def get_group_packages(self, group, grp_filter = None):
        ''' 
        get packages in a group 
        @param group: group id to get packages from
        @param grp_filter: group filters (Enum GROUP)
        '''
        self._send_command('get-group-packages', [group, str(grp_filter)])
        pkgs = self._get_list()
        return pkgs
        

    def get_repos(self):
        '''
        
        '''
        self._send_command('get-repos', [])
        data = self._get_list(':repo')
        repos = []
        for state, ident, name, gpg in data:
            gpg = gpg == 'True'
            state = state == 'True'
            elem = (state, ident, name, gpg)
            repos.append(elem)
        return repos
        
    def enable_repo(self, ident, state):
        '''
        
        @param ident:
        @param state:
        '''
        self._send_command('enable-repo', [ident, str(state)])
        args = self._get_result(':repo')
        return args
        
        
    def search(self, keys, filters):
        '''
        
        @param keys:
        @param filters:
        '''
        bKeys = pack(keys)
        bFilters = pack(filters)
        self._send_command('search', [bKeys, bFilters])
        pkgs = self._get_list()
        return pkgs

if __name__ == "__main__":
    pass

