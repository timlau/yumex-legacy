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
import time

import pexpect

from yumexbase.constants import *
from yumexbase import YumexBackendFatalError
from yumexbackend import  YumexPackage, pack, unpack

# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
from yumexbase import _, P_  # lint:ok
# pylint: enable-msg=W0611




#logginglevels._added_handlers = True # let yum think, that logging handlers is already added.


class YumClientBase:
    """ Client part of a the yum client/server """

    def __init__(self, frontend, timeout):
        '''

        @param timeout:
        '''
        self.child = None
        self.frontend = frontend
        self._timeout_value = timeout
        self._timeout_last = 0
        self._timeout_count = 0
        self.sending = False
        self.waiting = False
        self.end_state = None
        self.launcher_is_started = False
        self.yum_backend_is_running = False
        self.using_polkit = False

    def error(self, msg):
        """ error message (overload in child class)"""
        raise NotImplementedError()

    def warning(self, msg):
        """ warning message (overload in child class)"""
        raise NotImplementedError()

    def info(self, msg):
        """ info message (overload in child class)"""
        raise NotImplementedError()

    def debug(self, msg, name=None):
        """ debug message (overload in child class)"""
        raise NotImplementedError()

    def exception(self, msg):
        """ debug message (overload in child class)"""
        raise NotImplementedError()

    def yum_logger(self, msg):
        """ yum logger message (overload in child class)"""
        raise NotImplementedError()

    def _yum_logger(self, msg):
        '''
        unpack yum messages
        '''
        msg = unpack(msg)
        self.yum_logger(msg)

    def yum_state(self, state):
        """ yum state message handler (overload in child class)"""
        raise NotImplementedError()

    def lock_msg(self, state, additional):
        """ yum lock message handler (overload in child class)"""
        raise NotImplementedError()

    def exitcode(self, code):
        """ Exitcode from backend"""
        raise NotImplementedError()

    def launcher_quit(self):
        """ Exitcode from backend"""
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
        # Trigger the frontend fatal error handler
        self.frontend.handle_error(err, msg)

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

    def _launcher_cmd(self, cmd):
        param = pack(cmd)
        self._send_command("#run", [param])

    def _start_launcher(self, filelog, need_root):
        args = []
        if IS_PROD: # Bin package
            if os.getuid() == 0 or not need_root: # Root
                if need_root:
                    self.info(_('Client is running in rootmode, starting backend launcher directly'))
                cmd = '/usr/share/yumex/backend-launcher.py'
            else: # Non root run using console helper wrapper
                if self.frontend.settings.use_sudo:
                    self.info('Running backend launcher with sudo')
                    cmd = '/usr/bin/sudo'
                    args.append('-n') # Abort sudo if password is needed
                    args.append(MAIN_PATH + "/backend-launcher.py")

                else:
                    cmd = '/usr/bin/pkexec'
                    args.append('/usr/share/yumex/backend-launcher.py')
                    self.using_polkit = True

        else:
            if os.getuid() != 0 and need_root: # Non Root
                self.info('Running backend launcher with \"sudo %s\"' % (MAIN_PATH + "/backend-launcher.py"))
                cmd = '/usr/bin/sudo'
                args.append('-n') # Abort sudo if password is needed
                args.append(MAIN_PATH + "/backend-launcher.py")
            else: # root or not root needed
                if os.getuid() == 0:
                    self.info('ROOTMODE: Running backend launcher (%s)' % (MAIN_PATH + "/backend-launcher.py"))
                else:
                    self.info('Running backend launcher as non-root (%s)' % (MAIN_PATH + "/backend-launcher.py"))
                cmd = MAIN_PATH + "/backend-launcher.py"
        self.child = pexpect.spawn(cmd, args, timeout=self._timeout_value)
        self.child.setecho(False)
        if filelog:
            self.child.logfile_read = sys.stdout
        self._wait_for_launcher_started()
        self.launcher_is_started = True

    def setup(self, debuglevel=2, plugins=True, filelog=False, offline=False,
            repos=None, proxy=None, yum_conf='/etc/yum.conf', need_root=True):
        ''' Setup the client and spawn the server'''
        if not self.yum_backend_is_running:
            self.debug("Setup START")
            args = []
            if not self.launcher_is_started:
                self._start_launcher(filelog, need_root)
            cmd = MAIN_PATH + "/yum_childtask.py "
            args.append(str(debuglevel)) # debuglevel
            args.append(str(plugins))    # plugins
            args.append(str(offline))    # is offline
            args.append(str(yum_conf))    # is offline
            if repos:                    # enabled repos
                repo_str = ";".join(repos)
                args.append('"' + repo_str + '"')
            cmd_to_run = cmd + " ".join(args)
            self.debug("Command to run : " + cmd_to_run)
            self._launcher_cmd(cmd_to_run)
            self.debug("Setup END")
            return self._wait_for_started()
        else:
            return None

    def reset(self):
        """ reset the client"""
        if not self.yum_backend_is_running: # yum backend not running
            return True
        if not self.child.isalive():
            del self.child
            self.child = None
            return True
        else:
            cnt = 0
            while self.waiting and cnt < 5:
                self.debug("Trying to close the yum backend")
                time.sleep(1)
                cnt += 1
            if cnt < 10:
                rc = self._send_command('exit', [])
                if rc:
                    cmd, args = self._readline()
                    #self._close()
                    self.debug(cmd)
                    self.yum_backend_is_running = False
                    return True
        # The yum backend did not ended nicely
        self.error(_("Yum backend did not close nicely in time"))
        self.yum_backend_is_running = False
        self._close()
        return False


    def _send_command(self, cmd, args):
        """ send a command to the spawned server """
        line = "%s\t%s" % (cmd, "\t".join(args))
        debug_msg = 'Sending: %s args: %s' % (cmd, str(args))
        self.sending = True
        self.end_state = None
        while True:
            try:
                cmd, args = self._readline()
                if cmd == ':ready' or cmd == '#ready':
                    break
                elif cmd == None:
                    self.sending = False
                    return False
            except pexpect.TIMEOUT, e:  # lint:ok
                self._timeout()
                continue
        self.debug(debug_msg)
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
        if line.startswith('#') or line.startswith('&'):
            return line, []
        else:
            return None, line

    def _readline(self):
        ''' read a line from the server'''
        line = None
        if self.waiting: # Somebody else is already waiting for something
            return None, None
        while True and self.child.isalive():
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
            except pexpect.TIMEOUT, e:  # lint:ok
                self._timeout()
                continue
        # Client is not running any more
        # read messages in buffer and execute commands
        theend =  self.child.read().split("\n")
        for line in theend:
            cmd, args = self._parse_command(line)
            if cmd:
                self._check_for_message(cmd, args)
        self.child.close()
        exitrc = self.child.exitstatus
        # default error
        args = ['backend-not-running', pack(_('Backend not running as expected \n\nYum Extender will terminate\n   --> exit code : %s') % exitrc)]
        #polkit releated errors
        if self.using_polkit:
            if exitrc == 127:
                args = ['backend-not-running', pack(_('Could not get polkit autherisation to start backend \n\nYum Extender will terminate'))]
            elif exitrc == 126:
                args = ['backend-not-running', pack(_('User has cancelled polkit autherisation\n\nYum Extender will terminate'))]
        self.fatal(args)

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
            if len(args) > 1 and args[1] <> 'None':
                self.debug(args[0], args[1])
            else:
                self.debug(args[0])
        elif cmd == ':warning':
            self.warning(args[0])
        elif cmd == ':exception':
            self.exception(args[0])
        elif cmd == ':yum':
            self._yum_logger(args[0])
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
        elif cmd == ':lock':
            self.lock_msg(args[0], args[1])
        elif cmd == ':exitcode':
            self.exitcode(args[0])
        elif cmd == '&exit':
            self.launcher_quit()
        else:
            return False # not a message
        return True

    def _wait_for_started(self):
        '''

        '''
        if not self.child:
            return False
        beg = time.time()
        while not self.child.isalive():
            time.sleep(0.1)
            if time.time() - beg > 2:
                break
        cnt = 0
        while True and self.child.isalive():
            cmd, args = self._readline()
            cnt += 1
            if cmd == ':started':
                self.yum_backend_is_running = True
                return True
        return False

    def _wait_for_launcher_started(self):
        '''

        '''
        if not self.child:
            return False
        beg = time.time()
        while not self.child.isalive():
            time.sleep(0.1)
            if time.time() - beg > 2:
                break
        cnt = 0
        while True and self.child.isalive():
            cmd, args = self._readline()
            cnt += 1
            if cmd == '#started':
                return True
        return False

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

    def _get_list(self, result_cmd=":pkg"):
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
                cnt += 1
                po = YumexPackage(args, self.frontend, self)
                data.append(po)
                if (cnt % 250) == 0:
                    self.frontend.refresh()
            else:
                data.append(args)
        return data

    def _get_history_pkgs(self):
        '''
        read a list of :histpkg commands from the server, until and
        :end command is received
        '''
        data = []
        while True:
            cmd, args = self._readline()
            if self.is_ended(cmd, args):
                break
            if cmd == None: # readline is locked:
                break
            elif cmd == ':histpkg':
                po = unpack(args[0])
                data.append(po)
            else:
                data.append(args)
        return data

    def _get_packed_list(self, result_cmd):
        '''
        read a list of :hist commands from the server, until and
        :end command is received
        '''
        data = []
        while True:
            cmd, args = self._readline()
            if self.is_ended(cmd, args):
                break
            if cmd == None: # readline is locked:
                break
            elif not cmd == result_cmd:
                self.warning("_get_list unexpected command : %s (%s)" % (cmd, args))
            else:
                elem = unpack(args[0])
                data.append(elem)
        return data

    def _get_result(self, result_cmd):
        '''
        read a given result command from the server.
        '''
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
            if self.child.isalive():
                try:
                    self._send_command("#exit", []) # Send exit to backend launcher
                    beg = time.time()
                    while self.child.isalive():
                        time.sleep(0.1)
                        if time.time() - beg > 2:
                            break
                    self.debug("Forcing backend to close")
                    self.child.close(force=True)
                except pexpect.ExceptionPexpect, e:
                    del self.child
                    self.child = None
                    raise YumexBackendFatalError("backend-error", str(e))
            del self.child
        self.child = None
        self.launcher_is_started=False

    def execute_command(self, cmd , args=[]):
        '''
        Send a command to the backend and get a list of packages
        @param cmd:
        @param args:
        '''
        self._send_command(cmd, args)
        pkgs = self._get_list()
        return pkgs


    def filter_package_list(self, package_type, pkgs):
        '''
        Filter a list of packages based on a given package type
        package_type ::= all | installed | updates | available
        '''
        result = [];
        if package_type == 'updates':
            for pkg in pkgs:
                if pkg.is_update:
                    result.append(pkg)
        elif package_type == 'installed':
            for pkg in pkgs:
                if pkg.is_installed():
                    result.append(pkg)
        elif package_type == 'available':
            for pkg in pkgs:
                if not pkg.is_installed():
                    result.append(pkg)
        else:
            result = pkgs
        return result

class YumClient(YumClientBase):
    """
    Client part of a the yum client/server

    This class contains the actions used by the frontend

    """

    def __init__(self, frontend, timeout=.1):
        '''

        @param timeout:
        '''
        YumClientBase.__init__(self, frontend, timeout)

    def get_packages(self, pkg_filter, show_dupes=False, disable_cache=False):
        ''' get a list of packages based on pkg_filter '''
        return self.execute_command('get-packages',
                [str(pkg_filter), str(show_dupes), str(disable_cache)])

    def get_available_by_name(self, name):
        return self.execute_command('get-available-by-name', [name])

    def get_available_downgrades(self, po):
        return self.execute_command('get-available-downgrades', [po.id])

    def get_packages_size(self, ndx):
        ''' get a list of packages based on size range '''
        return self.execute_command('get-packages-size', [str(ndx)])

    def get_packages_repo(self, repoid):
        ''' get a list of packages based on repo '''
        return self.execute_command('get-packages-repo', [repoid])

    def get_history_packages(self, tid, data_set='trans_data'):
        ''' get a list of packages based on pkg_filter '''
        self._send_command('get-history-packages', [str(tid), data_set])
        pkgs = self._get_packed_list(result_cmd=':histpkg')
        return pkgs

    def get_history(self):
        ''' get a list of packages based on pkg_filter '''
        self._send_command('get-history', [])
        tids = self._get_packed_list(result_cmd=':hist')
        return tids

    def search_history(self, pattern):
        ''' get a list of packages based on pkg_filter '''
        self._send_command('search-history', [pack(pattern)])
        tids = self._get_packed_list(result_cmd=':hist')
        return tids

    def history_redo(self, tid):
        ''' reodo a history transaction '''
        self._send_command('history-redo', [str(tid)])
        return self._get_return_code()

    def history_undo(self, tid):
        ''' undo a history transaction '''
        self._send_command('history-undo', [str(tid)])
        return self._get_return_code()

    def set_option(self, option, value, on_repos=False):
        ''' get a list of packages based on pkg_filter '''
        self._send_command('set-option', [option, pack(value), pack(on_repos)])
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

    def get_update_info(self, ident, obsolete):
        self._send_command('update-info', [ident, pack(obsolete)])
        msgs = self._get_messages()
        if 'updateinfo' in msgs and 'updated_po' in msgs:
            return msgs['updateinfo'], msgs['updated_po']
        else:
            return (None, None)

    def backend_die(self):
        self._send_command('die',[])

    def add_transaction(self, ident, action):
        '''

        @param ident:
        @param action:
        '''
        return self.execute_command('add-transaction', [ident, action])

    def remove_transaction(self, ident, action):
        '''

        @param ident:
        @param action:
        '''
        return self.execute_command('remove-transaction', [ident])

    def list_transaction(self):
        '''

        '''
        return self.execute_command('list-transaction', [])

    def run_command(self, cmd, userlist):
        '''

        '''
        return self.execute_command('run-command', [cmd, pack(userlist)])

    def reset_transaction(self):
        '''

        '''
        self._send_command('reset-transaction', [])

    def build_transaction(self):
        '''

        '''
        self._send_command('build-transaction', [])
        msgs = self._get_messages()
        return msgs['return_code'][0], msgs['messages'], unpack(msgs['transaction'][0]), msgs['size']

    def run_transaction(self):
        '''

        '''
        self._send_command('run-transaction', [])
        lst = self._get_list()  # lint:ok
        return self.end_state

    def get_dependencies(self, po):
        '''

        '''
        rc = []
        self._send_command('get-dependencies', [po])
        reqs = self._get_packed_list(result_cmd=':req')
        for req, pkg_id in reqs:
            po = YumexPackage(pkg_id, self.frontend, self)
            rc.append((req, po))
        return rc

    def get_groups(self):
        '''

        '''
        self._send_command('get-groups', [])
        msgs = self._get_messages()
        return unpack(msgs['groups'][0])

    def get_group_packages(self, group, grp_filter=None):
        '''
        get packages in a group
        @param group: group id to get packages from
        @param grp_filter: group filters (Enum GROUP)
        '''
        return self.execute_command('get-group-packages', [group, str(grp_filter)])


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

    def enable_repo_persistent(self, ident, state):
        '''

        @param ident:
        @param state:
        '''
        self._send_command('enable-repo-persistent', [ident, str(state)])
        return self._get_return_code()

    def search(self, keys, filters, show_newest_only, package_type):
        '''

        @param keys:
        @param filters:
        '''
        bKeys = pack(keys)
        bFilters = pack(filters)
        show_newest_only = pack(show_newest_only)
        pkgs = self.execute_command('search', [bKeys, bFilters, show_newest_only])
        return self.filter_package_list(package_type, pkgs)

    def search_prefix(self, prefix, show_newest_only, package_type):
        '''
        Search for packages with prefix
        @param prefix prefix to search for
        '''
        show_newest_only = pack(show_newest_only)
        pkgs = self.execute_command('search-prefix', [prefix, show_newest_only])
        return self.filter_package_list(package_type, pkgs)

    def clean(self, what):
        '''

        @param ident:
        @param state:
        '''
        self._send_command('clean', [what])
        return self._get_return_code()


if __name__ == "__main__":
    pass

