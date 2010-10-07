#!/usr/bin/python -tt

import pynotify
import gtk
import os
import sys

MAIN_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
PIXMAPS_PATH = MAIN_PATH + '/../../gfx'
ICON_YUMEX = PIXMAPS_PATH + "/yumex-icon.png"

imageURI = 'file://' + ICON_YUMEX

class YumexStatusIcon(gtk.StatusIcon):
    def __init__(self, frontend):
        gtk.StatusIcon.__init__(self)
        self.frontend = frontend
        self.set_from_file(ICON_YUMEX)
        self.connect('popup-menu', self._on_right_click)
        self.connect('activate', self._on_left_click)
        self._hide = False
        self._menu = gtk.Menu()
        self._add_menu('Quit', self._quit)

    def hide(self):
        self.set_visible(False)

    def show(self):
        self.set_visible(True)


    def _on_right_click(self, data, event_button, event_time):
        self._show_menu(event_button, event_time, data)

    def _on_left_click(self, event):
        print('Left Click')

    def _quit(self, data):
        gtk.main_quit()

    def _add_menu(self, title, callback):
        item = gtk.MenuItem(title)
        #Append the menu items  
        self._menu.append(item)
        #add callbacks
        item.connect_object("activate", callback, None)
        item.show()


    def _show_menu(self, event_button, event_time, data=None):
        #Popup the menu   
        self._menu.popup(None, None, None, event_button, event_time)



class YumexNotification(pynotify.Notification):
    def __init__(self, title, body, status_icon):
        pynotify.init("Yum Extender")
        pynotify.Notification.__init__(self, title, body, imageURI)
        self.set_urgency(pynotify.URGENCY_NORMAL)
        self.set_timeout(pynotify.EXPIRES_DEFAULT)
        if status_icon:
            self.attach_to_status_icon(status_icon)

    def add_button(self, title):
        self.add_action("clicked", title, self.callback_function, title)

    def callback_function(self, notification=None, action=None, data=None):
         print "Notification Action: %s clicked" % data


def on_botton_clicked(widget, status=None):
    n = YumexNotification("Yum Extender", "Some information to the user", status)
    n.add_button('Ok')
    n.show()

if __name__ == "__main__":
    status = YumexStatusIcon(None)
    win = gtk.Window()
    win.connect('delete-event', gtk.main_quit)
    win.set_size_request(200, 50)
    button = gtk.Button("Python Notification Test")
    button.connect('clicked', on_botton_clicked, status)
    win.add(button)
    win.show_all()
    gtk.main()
