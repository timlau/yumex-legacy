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

from __future__ import with_statement

class UserDeniedError(Exception):
    'User has denied keyring authentication'

class CommandFailError(Exception):
    'Fail to execute a command'

def packed_env_string():
    import os
    env = dict( os.environ )
    env['PWD'] = os.getcwd()
    return repr(env)

def daemon():
    import dbus
    bus = dbus.SystemBus()
    obj = bus.get_object('org.yumex', '/')
    return obj

def get_dbus_daemon_version():
    ret = daemon().get_version(dbus_interface='org.yumex.Interface')
    return ret    

def restart_dbus_daemon():
    authenticate()
    daemon().exit(dbus_interface='org.yumex.Interface')

def get_authentication_method():
    ret = daemon().get_check_permission_method(dbus_interface='org.yumex.Interface')
    ret = int(ret)
    return ret

def authenticate():
    if get_authentication_method() == 0:
        import dbus, os
        bus = dbus.SessionBus()
        policykit = bus.get_object('org.freedesktop.PolicyKit.AuthenticationAgent', '/')
        policykit.ObtainAuthorization('org.yumex', dbus.UInt32(0), dbus.UInt32(os.getpid()))

def spawn_as_root(command):
    is_string_not_empty(command)
    
    authenticate()
    daemon().spawn(command, packed_env_string(), dbus_interface='org.yumex.Interface')

def get_version():
    authenticate()
    print daemon().get_version( dbus_interface='org.yumex.Interface')
    

def drop_priviledge():
    daemon().drop_priviledge(dbus_interface='org.yumex.Interface')
    
class AccessDeniedError(Exception):
    'User press cancel button in policykit window'

def run_as_root(cmd, ignore_error=False):
    import dbus
    is_string_not_empty(cmd)
    assert isinstance(ignore_error, bool)
    
    print '\x1b[1;33m', _('Run command:'), cmd, '\x1b[m'
    authenticate()
    try:
        daemon().run(cmd, packed_env_string(), timeout=36000, dbus_interface='org.yumex.Interface')
    except dbus.exceptions.DBusException, e:
        if e.get_dbus_name() == 'org.yumex.AccessDeniedError': raise AccessDeniedError(*e.args)
        elif e.get_dbus_name() == 'org.yumex.CommandFailError':
            if not ignore_error: raise CommandFailError(cmd)
        else: raise

def is_string_not_empty(string):
    if type(string)!=str and type(string)!=unicode: raise TypeError(string)
    if string=='': raise ValueError


def notify(title, content):
    'Show a notification in the right-upper corner.'
    # title must not be empty. 
    # otherwise, this error happens. notify_notification_update: assertion `summary != NULL && *summary != '\0'' failed
    assert isinstance(title, str) and title
    assert isinstance(content, str)
    try:
        import pynotify
        if not hasattr(notify,'ailurus_notify'):
            notify.ailurus_notify = pynotify.Notification(' ',' ')
        icon = D+'suyun_icons/notify-icon.png'
        if title == notify.ailurus_notify.get_property('summary'):
            notify.ailurus_notify = pynotify.Notification(title, content, icon)
            notify.ailurus_notify.set_hint_string("x-canonical-append", "")
        else:
            notify.ailurus_notify.update(title, content, icon)
               
        notify.ailurus_notify.set_timeout(10000)
        notify.ailurus_notify.show()
    except:
        print_traceback()


class CannotDownloadError(Exception):
    pass

class UserCancelInstallation(Exception):
    pass

if __name__ == '__main__':
    print('Getting deamon version')
    get_version()