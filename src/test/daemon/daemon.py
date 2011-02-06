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

from __future__ import with_statement
import dbus
import dbus.service
import dbus.glib
import gobject
import os
import subprocess
import ctypes
import gc

version = 100 # must be integer

class AccessDeniedError(dbus.DBusException):
    _dbus_error_name = 'org.yumex.AccessDeniedError'

class CommandFailError(dbus.DBusException):
    _dbus_error_name = 'org.yumex.CommandFailError'

class YumexDaemon(dbus.service.Object):

    def __init__(self, mainloop):
        self.mainloop = mainloop # use to terminate mainloop
        self.authorized_sender = set()
        bus_name = dbus.service.BusName('org.yumex', bus = dbus.SystemBus())
        dbus.service.Object.__init__(self, bus_name, '/')
        obj = dbus.SystemBus().get_object('org.freedesktop.PolicyKit1', '/org/freedesktop/PolicyKit1/Authority')
        obj = dbus.Interface(obj, 'org.freedesktop.PolicyKit1.Authority')

    @dbus.service.method('org.yumex.Interface', 
                                          in_signature='ss', 
                                          out_signature='', 
                                          sender_keyword='sender')
    def run(self, command, env_string, sender=None):
        ''' Run a command with root access '''
        self.check_permission(sender)
        command = command.encode('utf8')
        env_string = env_string.encode('utf8')
        env = self.__get_dict(env_string)
        try: 
            os.chdir(env['PWD'])
        except KeyError:
            raise KeyError(env, env_string) # help to fix issue 850
        task = subprocess.Popen(command, shell=True, env=env)
        task.wait()
        if task.returncode:
            raise CommandFailError(command, task.returncode)

    @dbus.service.method('org.yumex.Interface', 
                                          in_signature='', 
                                          out_signature='i') 
    def get_version(self):
        return version

    @dbus.service.method('org.yumex.Interface', 
                                          in_signature='', 
                                          out_signature='',
                                          sender_keyword='sender')
    def exit(self, sender=None):
        self.check_permission(sender)
        self.mainloop.quit()


    def check_permission(self, sender):
        if sender in self.authorized_sender:
            return
        else:
            self._check_permission(sender)
            self.authorized_sender.add(sender)


    def _check_permission(self, sender):
        if not sender: raise ValueError('sender == None')
        
        obj = dbus.SystemBus().get_object('org.freedesktop.PolicyKit1', '/org/freedesktop/PolicyKit1/Authority')
        obj = dbus.Interface(obj, 'org.freedesktop.PolicyKit1.Authority')
        (granted, _, details) = obj.CheckAuthorization(
                ('system-bus-name', {'name': sender}), 'org.yumex', {}, dbus.UInt32(1), '', timeout=600)
        if not granted:
            raise AccessDeniedError('Session is not authorized')

    def __get_dict(self, string):
        return eval(string)
    

    def __prepare_env(self, env_string):
        env_dict = self.__get_dict(env_string)
        if 'TERM' not in env_dict: env_dict['TERM'] = 'xterm'
        env_dict['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
        for key in ['DISPLAY', 'TERM', 'PATH']:
            os.putenv(key, env_dict[key])


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    mainloop = gobject.MainLoop()
    YumexDaemon(mainloop)
    mainloop.run()

if __name__ == '__main__':
    main()