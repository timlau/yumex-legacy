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
import codecs
import locale
import os
import signal
from yumexbackend.yum_clientserver import YumServer

my = None
def sigquit(signum, frame):
    if my:
        my.quit()
    sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGQUIT, sigquit)
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)
    sys.stdout.errors = 'replace'
    debuglevel = 2
    if len(sys.argv) > 2:
        debuglevel =  int(sys.argv[1])
        plugins =  sys.argv[2] == 'True'
        print ":debug\tUsing yum debuglevel = %i" % debuglevel
    my = YumServer(debuglevel,plugins)
    my.dispatcher()
