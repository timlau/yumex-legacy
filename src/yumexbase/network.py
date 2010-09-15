#!/usr/bin/env python
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# (C) 2009 Tim Lauridsen

'''
Yumex Networking Classes
'''

import dbus
from yumexbase.constants import *


class NetworkCheckBase:
    '''
    Network Check Base Class
    '''
    
    def __init__(self):
        self._connected = None
        self.logger = logging.getLogger(YUMEX_LOG)
       
    @property
    def is_connected(self):
        '''
        @return Network Connection State
                None : Network State is not detected
                True : Network Connected
                False : Network Disconnected
        '''
        return self._connected
    
    def check_network_connection(self):
        '''
        Update the network connection status
        @return True, if network connection  state could be detected
        '''
        raise NotImplementedError()
    
    
class NetworkCheckNetworkManager(NetworkCheckBase):
    '''
    Network Check Base Class
    '''
    
    def __init__(self):
        NetworkCheckBase.__init__(self)
    
    def check_network_connection(self):
        '''
        Update the network connection status
        @return True, if network connection  state could be detected
        '''
        try:
            bus = dbus.SystemBus()        
            self._connected = None
            nm = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
            dev = nm.GetDevices()
            for d in dev:
                net = bus.get_object('org.freedesktop.NetworkManager', d)
                net_props = dbus.Interface(net, 'org.freedesktop.DBus.Properties')
                props = net_props.GetAll('org.freedesktop.NetworkManager.Device')
                state = props['State']
                interface = "%s (%s)" % (props['Interface'],props['Driver'])
                if state == 8: # 8 = connected
                    #self.logger.info("network interface %s is connected" % interface)
                    self._connected = True
                else: # Disconnected or other not connected state
                    if self._connected == None:
                        self._connected = False
            return True
        except dbus.exceptions.DBusException,e: 
            # Could not get the state from NetworkManager
            # It might not be running
            return False

if __name__ == '__main__':
    nc = NetworkCheckNetworkManager()
    rc = nc.check_network_connection()
    if not rc:
        print "Network Connection could not be detected"
    else:
        if nc.is_connected:
            print("Network is connected")
        else:
            print("Network is disconnected")
            
        
