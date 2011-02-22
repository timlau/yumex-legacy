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
Test DBus gtk gui client 
"""


import os, gobject,dbus
from dbus.mainloop.glib import DBusGMainLoop
import gtk

class DBusClient(object):
    def __init__(self):
        # Do before session or system bus is created.
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        self.proxy = self.bus.get_object('dk.rasmil.MessageService',
          '/TestObject')
        self.control_interface = dbus.Interface(self.proxy,
          'dk.rasmil.MessageInterface')   
        self.bus.add_signal_receiver(self.on_message_recieved,
          dbus_interface="dk.rasmil.MessageInterface",
          signal_name="message_signal")

        win = gtk.Window()
        win.connect("delete_event", lambda w,e:gtk.main_quit())
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        
        self.text_message=gtk.Entry()
        set_message=gtk.Button("Set Message")
        display_message=gtk.Button("Display Welcome Message")
        set_message.connect("clicked", self.on_set_message_clicked)
        
        display_message.connect("clicked", 
            self.on_display_message_clicked)
        
        hbox.pack_start(set_message, False, True, 0)
        hbox.pack_start(display_message, False, True, 0)
        vbox.pack_start(self.text_message, False, True, 0)
        vbox.pack_start(hbox, False, True, 0)
        win.add(vbox)
        win.show_all()
    
    def on_message_recieved(self):
        print "message_signal caught"

    def on_set_message_clicked(self, widget):
        message = self.text_message.get_text()
        self.control_interface.set_message(message)

    def on_display_message_clicked(self, widget):
        print self.control_interface.display_welcome_message()

if __name__ == "__main__":
  app = DBusClient()
  gtk.main()
