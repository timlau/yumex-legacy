#!/usr/bin/env python

import gtk
import os
import sys
import time

# Paths
MAIN_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
PIXMAPS_PATH = MAIN_PATH + '/../../gfx'


def message(data=None):
    """
    Function to display messages to the user. 
    """

    msg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, data)
    msg.run()
    msg.destroy()



def open_app(data=None):
    icon.set_blinking(True)
    time.sleep(2)
    message(data)
    icon.set_blinking(False)

def close_app(data=None):
    message(data)
    gtk.main_quit()


def make_menu(event_button, event_time, data=None):
    menu = gtk.Menu()
    open_item = gtk.MenuItem("Open App")
    close_item = gtk.MenuItem("Close App")
    #Append the menu items  
    menu.append(open_item)
    menu.append(close_item)
    #add callbacks
    open_item.connect_object("activate", open_app, "Open App")
    close_item.connect_object("activate", close_app, "Close App")
    #Show the menu items   
    open_item.show()
    close_item.show()
    #Popup the menu   
    menu.popup(None, None, None, event_button, event_time)



def on_right_click(data, event_button, event_time):
    make_menu(event_button, event_time)



def on_left_click(event):
    message("Status Icon Left Clicked")



if __name__ == '__main__':
    icon = gtk.status_icon_new_from_file(PIXMAPS_PATH + '/yumex-icon.png')
    icon.connect('popup-menu', on_right_click)
    icon.connect('activate', on_left_click)
    gtk.main()
