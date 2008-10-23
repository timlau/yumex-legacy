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
import yum

class MyYumBase(yum.YumBase):
    
    def __init__(self):
        yum.YumBase.__init__(self)
        self.doConfigSetup()
    
    def _showPackage(self,pkg):
        sys.stdout.write("%s,%s,%s,%s,%s,%s,%s\n" % (pkg.name,pkg.epoch,pkg.ver,pkg.rel,pkg.arch,pkg.repoid,repr(pkg.summary)))
    
    def getAvailablePackages(self):
        for pkg in self.pkgSack.returnNewestByName():
            self._showPackage(pkg)
        print >> sys.stdout,':end'

    def getInstalledPackages(self):
        for pkg in self.rpmdb.getPackages():
            self._showPackage(pkg)
        print >> sys.stdout,':end'
        
    def _getPackage(self,para):
        n,e,v,r,a,id = para.split(';')
        if id == 'installed':
            pkgs = self.rpmdb.searchNevra(n,e,v,r,a)
        else:
            pkgs = self.pkgSack.searchNevra(n,e,v,r,a)
        if pkgs:
            return pkgs[0]
        else:
            return None
        
    def getAttribute(self,para):
        pkgstr,attr = para.split(',')
        po = self._getPackage(pkgstr)
        res = 'none'
        if po:
           if hasattr(po, attr):
               res = getattr(po, attr)
        sys.stdout.write("%s\n" % repr(res))
        
    def parseCommands(self):
        while True:
            line = raw_input('>')
            if ':' in line:
                cmd,para = line.split(':')
            else:
                cmd = line
            if cmd == 'quit':
                break
            elif cmd == 'get-available':
                self.getAvailablePackages()
            elif cmd == 'get-installed':
                self.getAvailablePackages()
            elif cmd == 'get-attr':
                self.getAttribute(para)


my = MyYumBase()
my.parseCommands()
