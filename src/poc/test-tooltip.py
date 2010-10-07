#!/usr/bin/python -tt

import gtk
import gobject
import os
import sys

MAIN_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
PIXMAPS_PATH = MAIN_PATH + '/../../gfx'
ICON_YUMEX = PIXMAPS_PATH + "/yumex-icon.png"

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


class TestTooptip:

    def __init__(self):
        self.status = YumexStatusIcon(None)
        self.progress = gtk.ProgressBar()
        self.fraction = 0.0
        self.progress.set_fraction(self.fraction)
        self.tooptip = self._setup_tooltip()
        win = gtk.Window()
        win.connect('delete-event', gtk.main_quit)
        win.set_size_request(200, 200)
        fancy_label = gtk.Label("A fancy Tooltip")
        fancy_label.props.has_tooltip = True
        fancy_label.connect("query-tooltip", self.on_query_tooltip)
        win.add(fancy_label)
        win.show_all()
        self.window = win
        gobject.timeout_add(250, self.update)
        gtk.main()


    def _setup_tooltip(self):
        vbox = gtk.VBox()
        vbox.set_spacing(5)
        label = gtk.Label('Fancy Tooltip with an Image')
        vbox.pack_start(label, False, False, 5)
        vbox.pack_start(self.progress, False, False, 5)
        vbox.show_all()
        return vbox

    def on_query_tooltip(self, widget, x, y, keyboard_tip, tooltip):
        tooltip.set_custom(self.tooptip)
        return True

    def update(self):
        print "pulse"
        self.fraction += 0.1
        if self.fraction > 1.0:
            self.fraction = 0.0
        self.progress.set_fraction(self.fraction)
        return True


if __name__ == "__main__":
    app = TestTooptip()
