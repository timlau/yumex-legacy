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

# Constants

from enum import Enum


# Package Types
PKG_TYPE = Enum('installed', 'available', 'update', 'obsolete')
# Package list filters
FILTER = Enum('all', 'installed', 'available', 'updates', 'obsoletes')
# Search filters
SEARCH = Enum('name', 'summary', 'description', 'ver', 'arch', 'repoid')
# Group Package filters
GROUP = Enum('all', 'minimum')
# State
STATE = Enum('none', 'init', 'download-meta', 'download-pkg', 'update', 'install', 'remove', 'cleanup')




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
        pass

    def get_progress(self):
        ''' Get the current progress element '''
        return self._progress

    def progress(self):
        ''' The Progress is updated'''
        pass

    def confirm_transaction(self, transaction):
        ''' confirm the current transaction'''
        pass

    def error(self, msg):
        ''' write an error message '''
        pass

    def info(self, msg):
        ''' write an info message '''
        pass

    def debug(self, msg):
        ''' write an debug message '''
        pass

    def warning(self, msg):
        ''' write an warning message '''
        pass

    def reset(self):
        ''' reset the frontend '''
        pass





