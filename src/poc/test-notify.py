#!/usr/bin/python -tt

import pynotify
import gtk

class YumexNotification(pynotify.Notification):
    def __init__(self, title, body):
        pynotify.init("Yum Extender")
        pynotify.Notification.__init__(self, title, body)
        self.set_urgency(pynotify.URGENCY_NORMAL)
        self.set_timeout(pynotify.EXPIRES_NEVER)

    def add_button(self, title):
        self.add_action("clicked", title, self.callback_function, title)

    def callback_function(self, notification=None, action=None, data=None):
         print "Notification Action: %s clicked" % data


if __name__ == "__main__":
    win = gtk.Window()
    win.connect('delete-event', gtk.main_quit)
    win.set_size_request(200, 50)
    fancy_label = gtk.Label("Python Notification Test")
    win.add(fancy_label)
    win.show_all()
    n = YumexNotification("Yum Extender", "Some information to the user")
    n.add_button('Ok')
    n.show()
    gtk.main()
