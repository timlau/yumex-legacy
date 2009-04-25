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
sys.path.insert(0, '/home/tim/udv/work/yumex/src')
import time

from guihelpers import Controller, doGtkEvents
from yumexgui.dialogs import Progress
#from yumexbase.constants import *

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
        Controller.__init__(self, BUILDER_FILE , 'main', domain = 'yumex', connect=False)
        self.window.set_title("Testing Progress")
        self.window.show()
        self.progress = Progress(self.ui, self.window)
        self.progress.show()
        doGtkEvents()
        self.run_tests()
        
    def run_tests(self):
        print self.ui.Progress.get_size()
        w,h = self.ui.Progress.get_size()
        self.progress.set_title("Testing Progress - Title")
        doGtkEvents()
        time.sleep(1)
        self.progress.set_header("Testing Progress - Header")
        doGtkEvents()
        time.sleep(1)
        self.progress.set_action("Testing Progress - Action")
        doGtkEvents()
        time.sleep(1)
        self.test_bar()
        self.test_tasks()
        doGtkEvents()
        print self.ui.Progress.get_default_size()
        self.ui.Progress.resize(w,h)

        self.test_bar()
        time.sleep(3)
        self.main_quit()
        
    def test_tasks(self):
        self.progress.show_tasks()
        for task_id in ('depsolve','download','gpg-check','test-trans','run-trans'):
            self.progress.tasks.set_state(task_id,TASK_RUNNING)
            self.test_bar(task_id)
            self.progress.tasks.set_state(task_id,TASK_COMPLETE)
        doGtkEvents()
        time.sleep(1)
        self.progress.hide_tasks()
        
    def test_bar(self,task_id=None):
        frac = 0.0
        while True:
            if frac > 0.99:
                percent = 100
                frac = 1.0
            else:
                percent = int(frac*100)
            self.progress.set_fraction(frac,"%i %%" % percent)
            self.progress.set_action("Processed %i %% of the action" % percent )
            if task_id:
                self.progress.tasks.set_extra_label(task_id,"%i %%" % percent)
            doGtkEvents()
            frac += 0.01
            time.sleep(0.05)
            if frac > 1.0:
                break
        self.progress.set_action("Action Completted")
        doGtkEvents()
        

if __name__ == "__main__":
    tp = TestProgress()        