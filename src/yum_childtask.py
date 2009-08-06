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
'''
The yum child task started by yumex in the background
'''

import sys
import signal
import os
from yumexbackend.yum_server import YumServer
import yum.misc

my = None
def sigquit(signum, frame):
    '''
    
    @param signum:
    @param frame:
    '''
    if my:
        my.quit()
    sys.exit(1)


if __name__ == "__main__":
    if os.getuid() != 0:
        print "yum_childtask.py need to be running as root"
        sys.exit(1)
    signal.signal(signal.SIGQUIT, sigquit)
    yum.misc.setup_locale() # setup the locales
    debuglevel = 2
    repos = []
    plugins = True
    if len(sys.argv) > 2:
        debuglevel = int(sys.argv[1])
        plugins = sys.argv[2] == 'True'
        if len(sys.argv) == 4:
            repos = sys.argv[3].split(';')
        else:
            repos = []
        print ":debug\tUsing yum debuglevel = %i" % debuglevel
    my = YumServer(debuglevel, plugins, repos)
    my.dispatcher()
