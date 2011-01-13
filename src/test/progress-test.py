#!/usr/bin/python
# Licensed under the GNU General Public License Version 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# Copyright (C) 2008
#    Tim Lauridsen <timlau@fedoraproject.org>

import sys
import gtk
import os.path
print os.path.expanduser('~/udv/work/yumex/src')
sys.path.insert(0, os.path.expanduser('~/udv/work/yumex/src'))
import time

from yumexbase.constants import *
from guihelpers import Controller, doGtkEvents
from yumexgui.dialogs import Progress, TransactionConfirmation

BUILDER_FILE = '../yumex.glade'
TASK_PENDING = 1
TASK_RUNNING = 2
TASK_COMPLETE = 3

class TestProgress(Controller):
    ''' This class contains all signal callbacks '''


    def __init__(self):
        '''
        Init the signal callback Controller 
        '''
        # init the Controller Class to connect signals etc.
        Controller.__init__(self, BUILDER_FILE , 'main', domain='yumex', connect=False)
        self.status_icon = None
        self.window.set_title("Testing Progress")
        self.window.show()
        self.progress = Progress(self)
        self.progress.show()
        doGtkEvents()
        self.run_tests()

    def run_tests(self):
        w, h = self.ui.Progress.get_size() # get the default size
        self.progress.set_title("Testing Progress - Title")
        doGtkEvents()
        time.sleep(1)
        self.progress.set_header("Testing Progress - Header")
        doGtkEvents()
        time.sleep(1)
        self.progress.set_action("Testing Progress - Action")
        doGtkEvents()
        time.sleep(1)
        #self.test_bar()
        #self.test_tasks()
        doGtkEvents()
        self.ui.Progress.resize(w, h) # shrink to the default size again
        self.progress.set_action("Testing Progress - Action")
        self.test_bar()
        self.test_show_hide()
        time.sleep(3)
        self.main_quit()

    def test_tasks(self):
        self.progress.tasks.reset()
        self.progress.show_tasks()
        self.progress.tasks.run_current() # task1 is now running
        for i in xrange(0,len(self.progress.tasks)):
            self.progress.set_header("%s" % self.progress.tasks.get_task_label())
            self.test_bar()
            self.progress.tasks.next()
            doGtkEvents()
        time.sleep(1)
        self.progress.hide_tasks()

    def test_bar(self, task_id=None):
        frac = 0.0
        while True:
            if frac > 0.99:
                percent = 100
                frac = 1.0
            else:
                percent = int(frac * 100)
            self.progress.set_fraction(frac, "%i %%" % percent)
            self.progress.set_action("Processed %i %% of the action" % percent)
            if task_id:
                self.progress.tasks.set_extra_label(task_id, "%i %%" % percent)
            doGtkEvents()
            frac += 0.01
            time.sleep(0.05)
            if frac > 1.0:
                break
        self.progress.set_action("Action Completed")
        doGtkEvents()
        
    def test_show_hide(self):
        self.progress.set_title("Testing Progress - Hide/Show")
        self.progress.set_action("Testing Progress - Action")
        self.progress.hide_progress()
        self.progress.hide_tasks()
        self._setup_extras()
        self.delay()
        self.progress.set_header("Show Progress")
        self.progress.show_progress()
        self.delay()
        self.progress.set_header("Show Tasks")
        self.progress.show_tasks()
        self.delay()
        self.progress.set_header("Hide Tasks")
        self.progress.hide_tasks()
        self.delay()
        
    def _setup_extras(self):
        tc = TransactionConfirmation(self.ui, self.window)
        #tc.dialog.show_all()
        widget = tc.dialog.vbox
        content = gtk.VBox()
        widget.reparent(content)
        self.ui.transactionEvent.hide()
        self.progress.show_extra(widget=content)
        
        
    def delay(self, time_to_sleep=5.0):
        steps = int(time_to_sleep / 0.1)
        for x in xrange(0,steps):
            doGtkEvents()
            time.sleep(0.1)
        

if __name__ == "__main__":
    tp = TestProgress()
