#!/usr/bin/python -tt

import pynotify

def callback_function(notification=None, action=None, data=None):
     print "It worked!"
     print notification, action, data

pynotify.init("Some Application or Title")
n = pynotify.Notification("Title", "body", "dialog-info")
n.set_urgency(pynotify.URGENCY_NORMAL)
n.set_timeout(pynotify.EXPIRES_NEVER)

n.add_action("clicked", "Open", callback_function, None)
n.add_action("clicked", "Close", callback_function, None)
n.show()
