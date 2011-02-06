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

version = 10 # must be integer

class AccessDeniedError(dbus.DBusException):
    _dbus_error_name = 'org.yumex.AccessDeniedError'

class CommandFailError(dbus.DBusException):
    _dbus_error_name = 'org.yumex.CommandFailError'

class CannotDownloadError(dbus.DBusException):
    _dbus_error_name = 'org.yumex.CannotDownloadError'

class YumexDeamon(dbus.service.Object):
    @dbus.service.method('org.yumex.Interface', 
                                          in_signature='ss', 
                                          out_signature='', 
                                          sender_keyword='sender')
    def run(self, command, env_string, sender=None):
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
                                          in_signature='ss', 
                                          out_signature='i', 
                                          sender_keyword='sender')
    def spawn(self, command, env_string, sender=None):
        self.check_permission(sender)
        command = command.encode('utf8')
        env_string = env_string.encode('utf8')
        env = self.__get_dict(env_string)
        os.chdir(env['PWD'])
        task = subprocess.Popen(command, shell=True, env=env)
        return task.pid

    @dbus.service.method('org.yumex.Interface', 
                                          in_signature='', 
                                          out_signature='i') 
    def get_check_permission_method(self):
        return self.check_permission_method

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
            self.__check_permission(sender)
            self.authorized_sender.add(sender)

    def __init__(self, mainloop):
        self.mainloop = mainloop # use to terminate mainloop
        self.authorized_sender = set()
        bus_name = dbus.service.BusName('org.yumex', bus = dbus.SystemBus())
        dbus.service.Object.__init__(self, bus_name, '/')
        self.lock1_fd = -1 # a fd
        self.lock2_fd = -1 # a fd
        obj = dbus.SystemBus().get_object('org.freedesktop.PolicyKit1', '/org/freedesktop/PolicyKit1/Authority')
        obj = dbus.Interface(obj, 'org.freedesktop.PolicyKit1.Authority')
        self.check_permission_method = 1

    def __check_permission(self, sender):
        # This function is from project "gnome-lirc-properties". Thanks !
        if not sender: raise ValueError('sender == None')
        
        obj = dbus.SystemBus().get_object('org.freedesktop.PolicyKit1', '/org/freedesktop/PolicyKit1/Authority')
        obj = dbus.Interface(obj, 'org.freedesktop.PolicyKit1.Authority')
        (granted, _, details) = obj.CheckAuthorization(
                ('system-bus-name', {'name': sender}), 'org.yumex', {}, dbus.UInt32(1), '', timeout=600)
        if not granted:
            raise AccessDeniedError('Session is not authorized. Authorization method = 1')

    def __get_dict(self, string):
        return eval(string)
    
    @dbus.service.method('org.yumex.Interface',
                                    in_signature='',
                                    out_signature='',
                                    sender_keyword='sender')
    def drop_priviledge(self, sender=None):
        if sender in self.authorized_sender:
            self.authorized_sender.remove(sender)

    def __prepare_env(self, env_string):
        env_dict = self.__get_dict(env_string)
        if 'TERM' not in env_dict: env_dict['TERM'] = 'xterm'
        env_dict['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
        for key in ['DISPLAY', 'TERM', 'PATH']:
            os.putenv(key, env_dict[key])


def main(): # revoked by yumex-daemon
    try:
        libc = ctypes.CDLL('libc.so.6')
        libc.prctl(15, 'yumex-daemon', 0, 0, 0) # change_task_name
    except: pass
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    mainloop = gobject.MainLoop()
    YumexDeamon(mainloop)
    mainloop.run()

if __name__ == '__main__':
    main()