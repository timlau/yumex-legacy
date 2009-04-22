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

class YumexProgressBase:
    '''
    A Virtual Progress class
    '''
    def __init__(self):
        self._active = False
        self._pulse = False
    
    def show(self):
        ''' Show the progress '''
        self._active = True
    
    def hide(self):
        ''' Hide the progress '''
        self._active = False
    
    def is_active(self):
        return self._active
    
    def is_pulse(self):
        return self._pulse
    
    def set_pulse(self, pulse):
        self._pulse = pulse
    
    def set_title(self, title):
        ''' set the progress dialog title '''
        raise NotImplementedError()
    
    def set_fraction(self, frac, text = None):
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

    def confirm_transaction(self, transaction):
        ''' confirm the current transaction'''
        raise NotImplementedError()

    def error(self, msg, exit_pgm):
        ''' write an error message '''
        raise NotImplementedError()

    def info(self, msg):
        ''' write an info message '''
        raise NotImplementedError()

    def debug(self, msg):
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
    def __init__(self, value = None):
        Exception.__init__(self)
        self.value = value
    
    def __str__(self):
        return "%s" % (self.value,)

class YumexBackendFatalError(YumexBaseError):
    def __init__(self, err, msg):
        YumexBaseError.__init__(self)
        self.err = err
        self.msg = msg
    



# from output.py (yum)
def format_number(number, si = 0, space = ' '):
    """Turn numbers into human-readable metric-like numbers"""
    symbols = ['', # (none)
                'k', # kilo
                'M', # mega
                'G', # giga
                'T', # tera
                'P', # peta
                'E', # exa
                'Z', # zetta
                'Y'] # yotta

    if si: 
        step = 1000.0
    else: 
        step = 1024.0

    thresh = 999
    depth = 0

    # we want numbers between 
    while number > thresh:
        depth = depth + 1
        number = number / step

    # just in case someone needs more than 1000 yottabytes!
    diff = depth - len(symbols) + 1
    if diff > 0:
        depth = depth - diff
        number = number * thresh ** depth

    if type(number) == type(1) or type(number) == type(1L):
        fmt = '%i%s%s'
    elif number < 9.95:
        # must use 9.95 for proper sizing.  For example, 9.99 will be
        # rounded to 10.0 with the .1f format string (which is too long)
        fmt = '%.1f%s%s'
    else:
        fmt = '%.0f%s%s'

    return(fmt % (number, space, symbols[depth]))



