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
import traceback

def _to_unicode( txt, encoding='utf-8'):
    if isinstance(txt, basestring):
        if not isinstance(txt, unicode):
            txt = unicode(txt, encoding, errors='replace')
    return txt

class ServerYumBase(yum.YumBase):
    
    def __init__(self):
        yum.YumBase.__init__(self)
        self.doConfigSetup()

    def write(self,msg):
        msg.replace("\n",";")
        sys.stdout.write("%s\n" % msg)    
    
    def _show_package(self,pkg):
        self.write(":pkg\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (pkg.name,pkg.epoch,pkg.ver,pkg.rel,pkg.arch,pkg.repoid,pkg.summary))
    
    def info(self,msg):
        self.write(":info\t%s" % msg)

    def error(self,msg):
        self.write(":error\t%s" % msg)

    def debug(self,msg):
        self.write(":debug\t%s" % msg)
    
    def warning(self,msg):
        self.write(":warning\t%s" % msg)

    def get_packages(self,pkg_narrow):
        if pkg_narrow:
            narrow = pkg_narrow[0]
            ygh = self.doPackageLists(pkgnarrow=narrow)
            for pkg in getattr(ygh,narrow):
                self._show_package(pkg)
        self.write(':end')
        
    def _getPackage(self,para):
        n,e,v,r,a,id = para
        if id == 'installed':
            pkgs = self.rpmdb.searchNevra(n,e,v,r,a)
        else:
            pkgs = self.pkgSack.searchNevra(n,e,v,r,a)
        if pkgs:
            return pkgs[0]
        else:
            return None
        
    def get_attribute(self,args):
        pkgstr = args[:-1]
        attr = args[-1]
        po = self._getPackage(pkgstr)
        res = 'none'
        if po:
            if hasattr(po, attr):
                res = getattr(po, attr)
                res = res.replace('\n',';')
        self.write(':attr\t%s' % str(res))

    def parse_command(self, cmd, args):
        if cmd == 'get-packages':
            self.get_packages(args)
        elif cmd == 'get-attribute':
            self.get_attribute(args)
        else:
            self.error('Unknown command : %s' % cmd)

    def dispatcher(self):
        try:
            while True:
                self.write(':ready')
                line = sys.stdin.readline().strip('\n')
                if not line or line == 'exit':
                    break
                args = line.split('\t')
                self.parse_command(args[0], args[1:])
        except:
            etype = sys.exc_info()[0]
            evalue = sys.exc_info()[1]
            etb = traceback.extract_tb(sys.exc_info()[2])
            errmsg = 'Error Type: %s ;' % str(etype)
            errmsg += 'Error Value: %s ;' % str(evalue)
            for tub in etb:
                f,l,m,c = tub # file,lineno, function, codeline
                errmsg += '  File : %s , line %s, in %s;' % (f,str(l),m)
                errmsg += '    %s ;' % c
            self.write(":exception\t%s" % errmsg)
            self.write(':end')
        sys.exit(1)

if __name__ == "__main__":
    import codecs
    import locale
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)
    sys.stdout.errors = 'replace'
    my = ServerYumBase()
    my.dispatcher()
