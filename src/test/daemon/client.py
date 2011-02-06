#coding: utf-8
#
# Ailurus - a simple application installer and GNOME tweaker
#
# Copyright (C) 2009-2010, Ailurus developers and Ailurus contributors
# Copyright (C) 2007-2010, Trusted Digital Technology Laboratory, Shanghai Jiao Tong University, China.
#
# Ailurus is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Ailurus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ailurus; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

#from __future__ import with_statement
import os
import dbus

class UserDeniedError(Exception):
    'User has denied keyring authentication'

class CommandFailError(Exception):
    'Fail to execute a command'

class AccessDeniedError(Exception):
    'User press cancel button in policykit window'
    
class YumexDaemonClient:    

    def __init__(self):
        self.daemon = self._get_daemon() 

    def packed_env_string(self):
        ''' Get at repr of the current evironment'''
        env = dict( os.environ )

        env['PWD'] = os.getcwd()
        return repr(env)

    def _get_daemon(self):
        ''' Get the yumex daemon dbus object'''
        obj = None
        try:
            bus = dbus.SystemBus()
            obj = bus.get_object('org.yumex', '/')
        except dbus.exceptions.DBusException, e:
            print "Initialize of dbus daemon failed"
            print str(e)
        return obj

    def get_daemon_version(self):
        ''' Get the daemon version '''
        ret = self.daemon.get_version(dbus_interface='org.yumex.Interface')
        return ret    

    def exit_daemon(self):
        ''' End the daemon'''
        self.daemon.exit(dbus_interface='org.yumex.Interface')

    def get_authentication_method(self):
        ''' Get the authentication method'''
        ret = self.daemon.get_check_permission_method(dbus_interface='org.yumex.Interface')
        ret = int(ret)
        print('Authentication Method : %i' % ret)
        return ret

    def get_version(self):
        print self.daemon.get_version( dbus_interface='org.yumex.Interface')
    

    def run_as_root(self, cmd, ignore_error=False):
        self.is_string_not_empty(cmd)
        assert isinstance(ignore_error, bool)
        
        print  ('Running as root : %s' % cmd)
        try:
            self.daemon.run(cmd, self.packed_env_string(), timeout=36000, dbus_interface='org.yumex.Interface')
        except dbus.exceptions.DBusException, e:
            if e.get_dbus_name() == 'org.yumex.AccessDeniedError': raise AccessDeniedError(*e.args)
            elif e.get_dbus_name() == 'org.yumex.CommandFailError':
                if not ignore_error: raise CommandFailError(cmd)
            else: raise

    def is_string_not_empty(self, string):
        if type(string)!=str and type(string)!=unicode: raise TypeError(string)
        if string=='': raise ValueError

if __name__ == '__main__':
    cli = YumexDaemonClient()
    try:
        print('Getting deamon version')
        cli.get_version()
        print('Running some test commands as root')
        cli.run_as_root('touch /root/yumex.txt')
        cli.run_as_root('touch /root/yumex1.txt')
        cli.run_as_root('touch /root/yumex2.txt')
        cli.run_as_root('touch /root/dummy/yumex3.txt') # This will fail
        cli.exit_daemon()
    except AccessDeniedError, e:
        print str(e)
    except CommandFailError, e:
        print "command failed : %s " % str(e)