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

"""
Test DBus gtk gui service 
"""

import os, gobject, dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gtk

output_label = None

class DBusObject(dbus.service.Object):
    
    # Display and message to gtk label and return message to caller 
    @dbus.service.method('dk.rasmil.MessageInterface',
      in_signature='', out_signature='s')
    def display_welcome_message(self):
        global output_label
        output_label.set_text("Welcome to dbus.")
        return "Welcome to dbus."

    # Set gtk label to the message that is passed 
    @dbus.service.method(dbus_interface='dk.rasmil.MessageInterface', in_signature='s', out_signature='')
    def set_message(self, s):
        global output_label
        if not isinstance(s, dbus.String):
            print "not string"
            return
        output_label.set_text(s)
        #emit signal
        self.message_signal()

    @dbus.service.signal('dk.rasmil.MessageInterface')
    def message_signal(self):
        return
    
def main():
      # Create GTK Gui 
      global output_label
      win = gtk.Window()
      win.connect("delete_event", lambda w,e:gtk.main_quit())
      output_label = gtk.Label("This message will change through using dbus.")
      win.add(output_label)
      win.show_all()
      
      # Start DBus Service
      dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
      session_bus = dbus.SessionBus()
      name = dbus.service.BusName("dk.rasmil.MessageService", session_bus)
      object = DBusObject(session_bus, "/TestObject")
      gtk.main() 
      
if __name__ == "__main__":
    main() 
      
    