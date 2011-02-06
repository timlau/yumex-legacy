#!/usr/bin/python -tt
#coding: utf-8
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
#
# (C) 2011 - Tim Lauridsen <timlau@fedoraproject.org>

import os
import dbus

DAEMON_ORG = 'org.yumex'
DAEMON_INTERFACE = 'org.yumex.Interface'

# Exception classes 
class CommandFailError(Exception):
    'Fail to execute a command'

class AccessDeniedError(Exception):
    'User press cancel button in policykit window'
    
class YumexDaemonClient:  
    ''' A class to communicate with a Yumex DBUS system service daemon '''  

    def __init__(self):
        self.daemon = self._get_daemon() 

    def _get_daemon(self):
        ''' Get the daemon dbus object'''
        obj = None
        try:
            bus = dbus.SystemBus()
            obj = bus.get_object(DAEMON_ORG, '/')
        except dbus.exceptions.DBusException, e:
            print "Initialize of dbus daemon failed"
            print str(e)
        return obj

    def exit(self):
        ''' End the daemon'''
        self.daemon.exit(dbus_interface=DAEMON_INTERFACE)

    def get_version(self):
        ''' get the daemon version'''
        return self.daemon.get_version( dbus_interface=DAEMON_INTERFACE)
    
    def run_as_root(self, cmd, ignore_error=False):
        ''' Use the daemon to run a command as root'''
        self._is_string_not_empty(cmd)        
        print  ('Running as root : %s' % cmd)
        try:
            env = self._packed_env_string()
            self.daemon.run(cmd, env, timeout=36000, dbus_interface=DAEMON_INTERFACE)
        except dbus.exceptions.DBusException, e:
            if e.get_dbus_name() == 'org.yumex.AccessDeniedError': raise AccessDeniedError(*e.args)
            elif e.get_dbus_name() == 'org.yumex.CommandFailError':
                if not ignore_error: raise CommandFailError(cmd)
            else: raise

    def _packed_env_string(self):
        ''' Get at repr of the current environment'''
        env = dict( os.environ )
        return repr(env)

    def _is_string_not_empty(self, string):
        ''' Check if a string is a string type and not empty'''
        if type(string)!=str and type(string)!=unicode: raise TypeError(string)
        if string=='': raise ValueError

if __name__ == '__main__':
    cli = YumexDaemonClient()
    try:
        print('Getting deamon version')
        print "Daemon Version : %i" % cli.get_version()
        print('Running some test commands as root')
        cli.run_as_root('touch /root/yumex.txt')
        cli.run_as_root('touch /root/yumex1.txt')
        cli.run_as_root('touch /root/yumex2.txt')
        cli.run_as_root('touch /root/dummy/yumex3.txt') # This will fail and raise CommandFailError
        cli.exit()
    except AccessDeniedError, e: # Catch if user press Cancel in the PolicyKit dialog
        print str(e)
    except CommandFailError, e:
        print "command failed : %s " % str(e)