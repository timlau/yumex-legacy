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

class ServerYumBase(yum.YumBase):
    
    def __init__(self):
        yum.YumBase.__init__(self)
        self.doConfigSetup()
    
    def _show_package(self,pkg):
        sys.stdout.write("PKG\t%s\t%s\t%s%s\t%s\t%s\t%s\n" % (pkg.name,pkg.epoch,pkg.ver,pkg.rel,pkg.arch,pkg.repoid,repr(pkg.summary)))
    
    def info(self,msg):
        sys.stdout.write("INFO\t%s" % msg)

    def error(self,msg):
        sys.stdout.write("ERROR\t%s" % msg)

    def debug(self,msg):
        sys.stdout.write("DEBUG\t%s" % msg)
    
    def warning(self,msg):
        sys.stdout.write("WARNING\t%s" % msg)

    def get_packages(self,pkg_narrow):
        if pkg_narrow == 'available':
            for pkg in self.pkgSack.returnNewestByName():
                self._show_package(pkg)
            print >> sys.stdout,':end'
        elif pkg_narrow == 'installed':
            for pkg in self.rpmdb.getPackages():
                self._show_package(pkg)
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
        
    def get_attribute(self,args):
        pkgstr,attr = args
        po = self._getPackage(pkgstr)
        res = 'none'
        if po:
            if hasattr(po, attr):
                res = getattr(po, attr)
        sys.stdout.write('ATTR\t%s\n' % repr(res))

    def parse_command(self, cmd, args):
        if cmd == 'get-available':
            self.get_packages('available')
        elif cmd == 'get-installed':
            self.get_packages('installed')
        elif cmd == 'get-attr':
            self.getAttribute(args)
        else:
            self.error('Unknown command : %s' % cmd)

    def dispatcher(self, args):
        while True:
            line = sys.stdin.readline().strip('\n')
            if not line or line == 'exit':
                break
            args = line.split('\t')
            self.parse_command(args[0], args[1:])
        sys.exit(1)


my = ServerYumBase()
my.parseCommands()
