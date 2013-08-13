#    Yum Exteder (yumex) - A GUI for yum
#    Copyright (C) 2013 Beat Kueng <beat-kueng@gmx.net>
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

from yumexbase.constants import *

import time


class UpdateTimestamp:
    '''
    a persistent timestamp. eg for storing the last update check
    '''

    def __init__(self, file_name=TIMESTAMP_FILE):
        self.time_file = file_name
        self.last_time = -1

    def get_last_time_diff(self):
        """
        returns time difference to last check in seconds >=0 or -1 on error
        """
        try:
            t = int(time.time())
            if self.last_time == -1:
                f = open(self.time_file, 'r')
                t_old = int(f.read())
                f.close()
                self.last_time = t_old
            if self.last_time > t: return -1
            return t - self.last_time
        except:
            pass
        return -1

    def store_current_time(self):
        t = int(time.time())
        f = open(self.time_file, 'w')
        f.write(str(t))
        f.close()
        self.last_time = t

