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

# interface base classes

'''
Yumex Backend Base Classes
'''

import time
import sys
import os.path

from kitchen.i18n import easy_gettext_setup

# setup the translation wrappers

_, P_  = easy_gettext_setup('yumex') 

class YumexProgressBase:
    '''
    A Virtual Progress class
    '''
    def __init__(self):
        '''
        
        '''
        self._active = False
        self._pulse = False

    def show(self):
        ''' Show the progress '''
        self._active = True

    def hide(self):
        ''' Hide the progress '''
        self._active = False

    def is_active(self):
        '''
        
        '''
        return self._active

    def is_pulse(self):
        '''
        
        '''
        return self._pulse

    def set_pulse(self, pulse):
        '''
        
        @param pulse:
        '''
        self._pulse = pulse

    def set_title(self, title):
        ''' set the progress dialog title '''
        raise NotImplementedError()

    def set_fraction(self, frac, text=None):
        ''' set the progress dialog title '''
        raise NotImplementedError()

    def set_header(self, text):
        ''' set the progress header text '''
        raise NotImplementedError()

    def set_action(self, text):
        ''' set the progress action text '''
        raise NotImplementedError()

    def pulse(self):
        ''' pulse the progress bar '''
        raise NotImplementedError()

    def reset(self):
        ''' reset the progress bar '''
        raise NotImplementedError()

class YumexFrontendBase:
    '''
    This is a frontend callback abstract class used by the backend and
    transaction to notify the frontend about changes.
    '''

    def __init__(self, backend, progress):
        ''' initialize the frontend'''
        self._backend = backend
        self._progress = progress

    def set_state(self, state):
        ''' Set the current state of work'''
        raise NotImplementedError()

    def get_progress(self):
        ''' Get the current progress element '''
        raise NotImplementedError()

    def set_progress(self, progress):
        ''' The Progress is updated'''
        raise NotImplementedError()

    def confirm_transaction(self, transaction, size):
        ''' confirm the current transaction'''
        raise NotImplementedError()

    def error(self, msg, exit_pgm):
        ''' write an error message '''
        raise NotImplementedError()

    def info(self, msg):
        ''' write an info message '''
        raise NotImplementedError()

    def debug(self, msg, name=None):
        ''' write an debug message '''
        raise NotImplementedError()

    def warning(self, msg):
        ''' write an warning message '''
        raise NotImplementedError()

    def exception(self, msg):
        ''' handle an expection '''
        raise NotImplementedError()

    def timeout(self, msg):
        ''' handle an timeout '''
        raise NotImplementedError()

    def reset(self):
        ''' reset the frontend '''
        raise NotImplementedError()

class YumexBaseError(Exception):
    """
    Base Yumex Error. All other Errors thrown by yum should inherit from
    this.
    """
    def __init__(self, value=None):
        '''
        
        @param value:
        '''
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        '''
        
        '''
        return "%s" % (self.value,)

class YumexBackendFatalError(YumexBaseError):
    '''
    
    '''
    def __init__(self, err, msg):
        '''
        
        @param err:
        @param msg:
        '''
        YumexBaseError.__init__(self, msg)
        self.err = err
        self.msg = msg


def TimeFunction(func):
    """
    This decorator catch yum exceptions and send fatal signal to frontend 
    """
    def newFunc(*args, **kwargs):
        t_start = time.time()
        rc = func(*args, **kwargs)
        t_end = time.time()
        name = func.__name__
        print("%s took %.2f sec" % (name, t_end - t_start))
        return rc

    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc


