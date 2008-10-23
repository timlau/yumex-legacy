#!/usr/bin/python -tt
# -*- coding: iso-8859-1 -*-
#    Yum Exteder (yumex) - A GUI for yum
#    Copyright (C) 2008 Tim Lauridsen < tim<AT>yum-extender<DOT>org >
#
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

# yum extender gui module

from gui import UI, Controller
from yumexbase import YumexFrontendBase
from misc import const

class YumexFrontend(YumexFrontendBase):
    '''
    Yumex Frontend  class

    This is a frontend callback class used by the backend and
    transaction to notify the frontend about changes.
    '''

    def __init__(self, backend, progress):
        ''' Setup the frontend callbacks '''
        self._backend = backend
        self._progress = progress

    def set_state(self, state):
        ''' set the state of work '''
        pass

    def get_progress(self):
        ''' Get the current progress object '''
        return self._progress

    def progress(self):
        ''' trigger at progress update'''
        pass

    def confirm_transaction(self, transaction):
        ''' confirm the current transaction'''
        pass

    def error(self, msg):
        ''' Write an error message to frontend '''
        pass

    def warning(self, msg):
        ''' Write an warning message to frontend '''
        pass

    def info(self, msg):
        ''' Write an info message to frontend '''
        pass

    def debug(self, msg):
        ''' Write an debug message to frontend '''
        pass

    def reset(self):
        ''' trigger a frontend reset '''
        pass


class YumexHandlers(Controller):
    ''' This class contains all glade signal callbacks '''
    
    
    def __init__(self):
        # Create and ui object contains the widgets.
        ui = UI(const.GLADE_FILE , 'main', 'yumex')
        # init the Controller Class to connect signals.
        Controller.__init__(self, ui)


class YumexApplication(YumexHandlers, YumexFrontend):
    """
    The Yum Extender main application class 
    """
    
    def __init__(self):
        self.backend = None
        self.progress = None
        self.setup_backend()
        YumexHandlers.__init__(self)
        YumexFrontend(self, self.backend, self.progress)
    
    def setup_backend(self):
        #TODO: Add some reel backend setup code
        self.backend = None
        self.progress = None
        