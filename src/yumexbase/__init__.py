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

import os
import sys
import pango
import time
from enum import Enum
from yumexbase.i18n import _

# Constant

__yumex_version__   = "2.1.0" 

YUMEX_LOG = 'yumex.verbose'
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
# Actions
ACTIONS = {0 : 'u', 1: 'i', 2 : 'r'}
FILTER_ACTIONS = {str(FILTER.updates) : 'u', str(FILTER.available): 'i', str(FILTER.installed) : 'r'}

# Paths
MAIN_PATH = os.path.abspath( os.path.dirname( sys.argv[0] ) )
BUILDER_FILE = MAIN_PATH+'/yumex.xml'  
if MAIN_PATH == '/usr/share/yumex':    
    PIXMAPS_PATH = '/usr/share/pixmaps/yumex'
else:
    PIXMAPS_PATH = MAIN_PATH+'/../gfx'

# icons
ICON_YUMEX      = PIXMAPS_PATH+"/yumex-icon.png"
ICON_PACKAGES   = PIXMAPS_PATH+'/button-packages.png'
ICON_GROUPS     = PIXMAPS_PATH+'/button-group.png'
ICON_QUEUE      = PIXMAPS_PATH+'/button-queue.png'
ICON_OUTPUT     = PIXMAPS_PATH+'/button-output.png'
ICON_REPOS      = PIXMAPS_PATH+'/button-repo.png'
    
#
PKG_FILTERS_STRINGS = (_('updates'),_('available'),_('installed'))
PKG_FILTERS_ENUMS = (FILTER.updates, FILTER.available, FILTER.installed)

REPO_HIDE = ['source','debuginfo']

RECENT_LIMIT = time.time() - (3600 * 24 * 14)
# Fonts
XSMALL_FONT = pango.FontDescription("sans 6")    
SMALL_FONT = pango.FontDescription("sans 8")    
BIG_FONT = pango.FontDescription("sans 12")    

# interface base classes

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

    def exception(self, msg):
        ''' handle an expection '''
        pass

    def timeout(self, msg):
        ''' handle an timeout '''
        pass

    def reset(self):
        ''' reset the frontend '''
        pass





