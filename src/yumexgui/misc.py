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

# Yumex misc classes & functions

import os
import sys

class const:
    ''' This Class contains all the Constants in Yumex'''
    __yumex_version__   = "2.1.0" 
    # Paths
    MAIN_PATH = os.path.abspath( os.path.dirname( sys.argv[0] ) )
    GLADE_FILE = MAIN_PATH+'/yumex.glade'  
    if MAIN_PATH == '/usr/share/yumex':    
        PIXMAPS_PATH = '/usr/share/pixmaps/yumex'
    else:
        PIXMAPS_PATH = MAIN_PATH+'/../gfx'
    

