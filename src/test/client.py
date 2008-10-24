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

import pexpect

class Package:
    def __init__(self,pkgstr):
        v = pkgstr.split(',')
        self.name   = v[0]
        self.epoch  = v[1]
        self.ver    = v[2]
        self.rel    = v[3]
        self.arch   = v[4]
        self.repoid = v[5]
        self.summary= v[6]
        
    def __str__(self):
        if self.epoch == '0':
            return '%s-%s-%s.%s' % (self.name,self.ver,self.rel,self.arch)
        else:
            return '%s:%s-%s-%s.%s' % (self.epoch,self.name,self.ver,self.rel,self.arch)
            
    def getPara(self):        
        return '%s;%s;%s;%s;%s;%s' % (self.name,self.epoch,self.ver,self.rel,self.arch,self.repoid)

class ClientYum:
    def __init__(self):
        self.child = pexpect.spawn('./yum_server.py')
        self.child.setecho(False)
        
    def _send_command(self,cmd):        
        self.child.sendline(cmd)
        
    def _get_list(self):
        pkgs = []
        while True:
            line = self.child.readline()
            if line.startswith(':end'):
                break
            else:
                p = Package(line.strip('\n'))
                pkgs.append(p)
        return pkgs
    
    def close(self):        
        self.child.close(force=True)
        
    def getAvailable(self):        
        self._send_command('get-available')
        pkgs = self._get_list()
        return pkgs

    def getInstalled(self):        
        self._send_command('get-installed')
        pkgs = self._get_list()
        return pkgs
    
    def getAttribute(self,pkg,attr):
        cmd = 'get-attr:%s,%s' % (pkg.getPara(),attr)
        self._send_command(cmd)
        line = self.child.readline()
        return line.strip('\n')
        
if __name__ == "__main__":    
    yc = ClientYum()
    pos = yc.getInstalled()
    for po in pos:
        print po
        print yc.getAttribute(po, 'description')
    yc.close()    
        
        