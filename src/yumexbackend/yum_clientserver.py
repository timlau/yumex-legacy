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

# Constants

import sys
import yum
import traceback
import pickle
import base64
import pexpect

class YumPackage:
    def __init__(self,base,args):
        self.base = base
        self.name   = args[0]
        self.epoch  = args[1]
        self.ver    = args[2]
        self.rel    = args[3]
        self.arch   = args[4]
        self.repoid = args[5]
        self.summary= args[6]
        
    def __str__(self):
        if self.epoch == '0':
            return '%s-%s-%s.%s' % (self.name,self.ver,self.rel,self.arch)
        else:
            return '%s:%s-%s-%s.%s' % (self.epoch,self.name,self.ver,self.rel,self.arch)

    @property        
    def id(self):        
        return '%s\t%s\t%s\t%s\t%s\t%s' % (self.name,self.epoch,self.ver,self.rel,self.arch,self.repoid)

    def get_attribute(self,attr):
        return self.base.get_attribute(self.id,attr)
    
class YumClient:
    """ Client part of a the yum client/server """

    def __init__(self):
        pass

    def error(self,msg):
        """ error message """
        print "Error:", msg

    def warning(self,msg):
        """ warning message """
        print "Warning:", msg

    def info(self,msg):
        """ info message """
        print "Info:", msg
    
    def debug(self,msg):
        """ debug message """
        print "Debug:", msg

    def exception(self,msg):
        """ debug message """
        print "Exception:", msg

    def setup(self):
        ''' Setup the backend'''
        self.child = pexpect.spawn('./yum_server.py')
        self.child.setecho(False)

    def reset(self):
        self._close()

    def _send_command(self,cmd,args):
        line = "%s\t%s" % (cmd,"\t".join(args))
        self.child.expect(':ready')        
        self.child.sendline(line)

    def _parse_command(self,line):
        if line.startswith(':'):
            parts = line.split('\t')
            cmd = parts[0]
            if len(parts) > 1:
                args = parts[1:]
            else:
                args = []
            return cmd,args
        else:
            return None,line
        
    def _check_for_message(self,cmd,args):
        if cmd == ':error':
            self.error(args[0])    
        elif cmd == ':info':
            self.info(args[0])    
        elif cmd == ':debug':
            self.debug(args[0])    
        elif cmd == ':warning':
            self.warning(args[0])
        elif cmd == ':exception':
            self.exception(args[0])
        else:
            return False # not a message
        return True    
        
    def _get_list(self):
        pkgs = []
        cnt = 0L
        while True:
            line = self.child.readline()
            if line.startswith(':end'):
                break
            cmd,args = self._parse_command(line)
            if cmd:
                if not self._check_for_message(cmd, args):
                    if cmd == ':pkg':
                        p = YumPackage(self,args)
                        pkgs.append(p)
        return pkgs

    def _get_result(self,result_cmd):
        cnt = 0L
        while True:
            line = self.child.readline()
            cmd,args = self._parse_command(line)
            if cmd:
                if not self._check_for_message(cmd, args):
                    if cmd == result_cmd:
                        return args
                    else:
                        self.frontend.warning("unexpected command : %s (%s)" % (cmd,args))
    
    def _close(self):        
        self.child.close(force=True)
        
    def get_packages(self,pkg_filter):    
        self._send_command('get-packages',[str(pkg_filter)])
        pkgs = self._get_list()
        return pkgs

    def get_attribute(self,id,attr):    
        self._send_command('get-attribute',[id,attr])
        args = self._get_result(':attr')
        if args:
            return pickle.loads(base64.b64decode(args[0]))
        else:
            return None


class YumServer(yum.YumBase):
    
    def __init__(self):
        yum.YumBase.__init__(self)
        self.doConfigSetup(errorlevel=0,debuglevel=0)

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
                res = base64.b64encode(pickle.dumps(res))
        self.write(':attr\t%s' % res)

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
    pass

