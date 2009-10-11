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
'''
Main Yum Extender Executable
'''
import sys
import os
import traceback
from yumexgui import YumexApplication


if os.environ.has_key('YUMEX_BACKEND') and os.environ['YUMEX_BACKEND'] == 'dummy':
    from yumexbackend.dummy_backend import YumexBackendDummy as backend 
else:
    from yumexbackend.yum_backend import YumexBackendYum as backend 

if os.getuid() == 0:
    print "Don't run yumex as root"
    sys.exit(1)

print "running"

import gettext
gettext.bindtextdomain("yumex", "/usr/share/locale")
gettext.textdomain("yumex")

debug = []
if 'YUMEX_DBG' in os.environ:
    debug = os.environ['YUMEX_DBG'].lower().split(',') 
    print debug
    
try:    
    app = YumexApplication(backend)
    app.debug_options = debug
    #app.run_test()
    app.run()
except SystemExit,e:
    print "Program Terminated"    
    sys.exit(1)
except: # catch other exception and write it to the logger.
    errmsg = traceback.format_exc()
    try:
        app.exception(errmsg)
    except:
        print errmsg
    sys.exit(1)
sys.exit(0)
