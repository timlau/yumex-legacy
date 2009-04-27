#!/usr/bin/python -tt
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
#
# (C) 2009 - Tim Lauridsen <timlau@fedoraproject.org>

'''
'''

import os
import os.path
import sys
sys.path.insert(0, '/usr/share/yum-cli')

import yum
import traceback
from optparse import OptionParser

from yum.packageSack import packagesNewestByNameArch

from yumexbase.constants import *
from yumexbackend.yum_client import pack, unpack
from urlgrabber.progress import format_number
import yum.logginglevels as logginglevels
import yum.Errors as Errors
from yum.rpmtrans import RPMBaseCallback
from yum.packages import YumLocalPackage
# Pylint in F10 cant handle the init_hook, so disable the cant find output error
# pylint: disable-msg=F0401
from output import DepSolveProgressCallBack # yum cli output.py
# pylint: enable-msg=F0401
from yum.constants import *
from yum.callbacks import *
import yumexbase.constants as const
import yum.plugins

from yum.i18n import _ as yum_translated 

# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
import logging
from yumexbase.i18n import _, P_
# pylint: enable-msg=W0611


class _YumPreBaseConf:
    """This is the configuration interface for the YumBase configuration.
       So if you want to change if plugins are on/off, or debuglevel/etc.
       you tweak it here, and when yb.conf does it's thing ... it happens. """

    def __init__(self):
        self.fn = '/etc/yum/yum.conf'
        self.root = '/'
        self.init_plugins = True
        self.plugin_types = (yum.plugins.TYPE_CORE,)
        self.optparser = None
        self.debuglevel = None
        self.errorlevel = None
        self.disabled_plugins = None
        self.enabled_plugins = None
        self.syslog_ident = None
        self.syslog_facility = None
        self.syslog_device = '/dev/log'

class YumServer(yum.YumBase):
    """ 
    A yum server class to be used in a spawned process.
    it receives commands from stdin and send results and info
    to stdout.
    
    Commands: (commands and parameters are separated with '\t' )
        get-packages <pkg-filter>            : get a list of packages based on a filter
        get-attribute <pkg_id> <attribute>   : get an attribute of an package
        add-transaction <pkg_id> <action>    : add a po to the transaction
        remove-transaction <pkg_id>          : add a po to the transaction
        list-transaction                     : list po's in transaction
        build-transaction                    : build the transaction (resolve dependencies)
        run-transaction                      : run the transaction
        get-groups                           : Get the groups
        get-repos                            : Get the repositories
        enable-repo                          : enable/disable a repository
        search                               : search
    
        Parameters:
        <pkg-filter> : all,installed,available,updates,obsoletes
        <pkg_id>     : name epoch ver release arch repoid ('\t' separated)
        <attribute>  : pkg attribute (ex. description, changelog)
        <action>     : 'install', 'update', 'remove' 
         
    Results:(starts with and ':' and cmd and parameters are separated with '\t')
    
        :info <message>        : information message
        :error <message>       : error message
        :warning <message>     : warning message
        :debug <message>       : debug message
        :exception <message>   : exception message
        :yum <message>         : yum logger message
        :pkg <pkg>             : package
        :end                   : end of package list command
        :attr <object>         : package object attribute
        :group <grp>           : group
        :repo <repo>           : repo
        :msg <type> <value>
        
        Parameters:
        <message>  : a text message ('\n' is replaced with ';'
        <pkg>      : name epoch ver release arch repoid summary ('\t' separated)
        <object>   : an package attribute pickled and base64 encoded.
      
    
    """
    
    def __init__(self, debuglevel = 2, plugins = True, enabled_repos = None):
        '''  Setup the spawned server '''
        yum.YumBase.__init__(self)
        parser = OptionParser()
        # Setup yum preconfig options
        self.preconf.debuglevel = debuglevel
        self.preconf.init_plugins = plugins
        self.preconf.optparser = parser
        # Disable refresh-package plugin, it will get in the way every time we finish a transaction
        self.preconf.disabled_plugins = ['refresh-packagekit']
        logginglevels.setLoggingApp('yumex')
        self.doLock()
        self.dnlCallback = YumexDownloadCallback(self)
        self.repos.setProgressBar(self.dnlCallback)
        # make some dummy options,args for yum plugins
        (options, args) = parser.parse_args()
        self.plugins.setCmdLine(options, args)
        dscb = DepSolveProgressCallBack()
        self.dsCallback = dscb
        if enabled_repos:
            for repo in self.repos.repos.values():
                if repo.id in enabled_repos:
                    self.repos.enableRepo(repo.id)
                else:
                    self.repos.disableRepo(repo.id)
                
        self.write(':started') # Let the front end know that we are up and running



    def doLock(self, lockfile = YUM_PID_FILE):
        '''
        Active the yum lock.
        @param lockfile: path to yum lock file
        '''
        cnt = 0
        nmsg = ""
        while cnt < 6:
            try:
                yum.YumBase.doLock(self)
                return True
            except Errors.LockError, e:
                self.warning(_("Yum is locked : ") + e.msg)
                if hasattr(e, 'pid'):
                    ps = self.get_process_info(e.pid)
                    if ps:
                        if ps['name'] == 'yumBackend.py':
                            nmsg = _("  The other application is: PackageKit")
                        else:
                            nmsg = _("  The other application is: %s") % ps['name']
                        self.warning(nmsg)
                self.warning(_("Waiting 10 seconds and tries again !!!"))
                cnt += 1
                time.sleep(10)
        msg = e.msg + "\n" + nmsg
        self.fatal("lock-error", msg)        

    def get_process_info(self, pid):
        '''
        Get process information from /proc 
        @param pid: the process id
        '''
        if not pid:
            return None

        # Maybe true if /proc isn't mounted, or not Linux ... or something.
        if (not os.path.exists("/proc/%d/status" % pid) or
            not os.path.exists("/proc/stat") or
            not os.path.exists("/proc/%d/stat" % pid)):
            return None

        ps = {}
        for line in open("/proc/%d/status" % pid):
            if line[ - 1] != '\n':
                continue
            data = line[: - 1].split(':\t', 1)
            if data[1].endswith(' kB'):
                data[1] = data[1][: - 3]
            ps[data[0].strip().lower()] = data[1].strip()
        return ps
                
    def quit(self):
        '''
        Exit the yum backend
        '''
        self.debug("Closing rpm db and releasing yum lock  ")
        self.closeRpmDB()
        self.doUnlock()
        self.ended(True)
        sys.exit(1)

    def write(self, msg):
        ''' write an message to stdout, to be read by the client'''
        msg.replace("\n", ";")
        sys.stdout.write("%s\n" % msg)    
        
    def _get_recent(self, po):
        '''
        get the recent state of a package
        @param po: yum package object
        '''
        if po.repoid == 'installed':
            ftime = int(po.returnSimple('installtime'))
        else:
            ftime = int(po.returnSimple('filetime'))
        if ftime > RECENT_LIMIT:
            return 1
        else:
            return 0
                    
    
    def _show_package(self, pkg, action = None):
        ''' write package result'''
        summary = pack(pkg.summary)
        recent = self._get_recent(pkg)
        action = pack(action)
        self.write(":pkg\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % 
                   (pkg.name, pkg.epoch, pkg.ver, pkg.rel, pkg.arch, pkg.repoid, 
                    summary, action, pkg.size, recent))
        
    def _show_group(self, grp):
        '''
        send a group message to the frontend
        @param grp: group object
        '''
        self.write(":group\t%s\t%s\t%s" % (grp.cat, grp.id, grp.name))

    def _show_repo(self, repo):
        '''
        send a repo message to the frontend        
        @param repo: repo object
        '''
        self.write(":repo\t%s\t%s\t%s\t%s" % (repo.enabled, repo.id, repo.name, repo.gpgcheck))

    def info(self, msg):
        ''' write an info message '''
        self.write(":info\t%s" % msg)

    def error(self, msg):
        ''' write an error message '''
        self.write(":error\t%s" % msg)

    def debug(self, msg):
        ''' write an debug message '''
        self.write(":debug\t%s" % msg)
    
    def warning(self, msg):
        ''' write an warning message '''
        self.write(":warning\t%s" % msg)

    def fatal(self, err, msg):
        ''' write an fatal message '''
        msg = pack(msg)
        self.write(":fatal\t%s\t%s" % (err, msg))
        sys.exit(1)
        
    def gpg_check(self, po, userid, hexkeyid):
        ''' write an fatal message '''
        value = (str(po), userid, hexkeyid)
        value = pack(value)
        self.write(":gpg-check\t%s" % (value))

    def message(self, msg_type, value):
        '''
        send at a custom message to the frontend
        @param msg_type: message type 
        @param value: some standard python object (dict,list,tuble etc.) to pass with the message.
        '''
        value = pack(value)
        self.write(":msg\t%s\t%s" % (msg_type, value))

    def yum_rpm(self, action, package, frac, ts_current, ts_total):
        ''' write an yum rpm action progressmessage '''
        value = (action, package, frac, ts_current, ts_total)
        value = pack(value)
        self.write(":yum-rpm\t%s" % value)
        
    def yum_dnl(self, ftype, name, percent):
        '''
        send an yum download progress message to the frontend
        @param ftype: filetype ('PKG' or 'REPO')
        @param name: filename
        @param percent: percent complette
        '''
        value = (ftype, name, percent)
        value = pack(value)
        self.write(":yum-dnl\t%s" % value)
        
    def yum_state(self, state):
        '''
        Send an yum transaction state message
        @param state: 
        '''
        self.write(":yum-state\t%s" % state)
       
    def yum_logger(self, msg):
        ''' write an yum logger message '''
        self.write(":yum\t%s" % msg)
        
    def ended(self, state):
        '''
        Send and ended message
        used to signal the end of a process
        @param state: the exit state of the process (True/False)
        '''
        state = pack(state)
        self.write(":end\t%s" % state)
        

    def get_packages(self, narrow):
        '''
        get list of packages and send results 
        @param narrow:
        '''
        
        if narrow:
            action = const.FILTER_ACTIONS[narrow]
            ygh = self.doPackageLists(pkgnarrow = narrow)
            for pkg in getattr(ygh, narrow):
                self._show_package(pkg, action)
            del ygh
        self.ended(True)
        
    def _getPackage(self, para):
        ''' find the real package from an package id'''
        n, e, v, r, a, ident = para
        if ident == 'installed':
            pkgs = self.rpmdb.searchNevra(n, e, v, r, a)
        else:
            repo = self.repos.getRepo(ident) # Used the repo sack, it will be faster
            if repo:
                pkgs = repo.sack.searchNevra(n, e, v, r, a)
            else: # fallback to the use the pkgSack, just in case
                pkgs = self.pkgSack.searchNevra(n, e, v, r, a)
        if pkgs:
            return pkgs[0]
        else:
            return None
        
    def get_attribute(self, args):
        ''' get a package attribute and send the result '''
        pkgstr = args[: - 1]
        attr = args[ - 1]
        po = self._getPackage(pkgstr)
        res = pack(None)
        if po:
            res = getattr(po, attr)
            res = pack(res)
        self.write(':attr\t%s' % res)

    def get_changelog(self, args):
        ''' get a given number of changelog lines '''
        pkgstr = args[: - 1]
        num = int(args[ - 1])
        po = self._getPackage(pkgstr)
        res = []
        if po:
            clog = getattr(po, 'changelog')
            if num != 0:
                i = 0
                for (c_date, c_ver, msg) in po.changelog:
                    i += 1
                    elem = (c_date, c_ver, msg)
                    res.append(elem)
                    if i == num: 
                        break
            else:
                res = clog    
            res = pack(res)
        self.write(':attr\t%s' % res)
        
    def add_transaction(self, args):
        '''
        
        @param args:
        '''
        pkgstr = args[: - 1]
        action = args[ - 1]
        po = self._getPackage(pkgstr)
        txmbrs = []
        if action == "install":
            txmbrs = self.install(po)
        elif action == "update":
            txmbrs = self.update(po)
        elif action == "remove":
            txmbrs = self.remove(po)
        for txmbr in txmbrs:
            self._show_package(txmbr.po, txmbr.ts_state)
            self.debug("Added : " + str(txmbr))            
        self.ended(True)
            
    def remove_transaction(self, args):
        '''
        
        @param args:
        '''
        pkgstr = args
        po = self._getPackage(pkgstr)
        self.tsInfo.remove(po)

    def list_transaction(self):
        '''
        
        '''
        for txmbr in self.tsInfo:
            self._show_package(txmbr.po, txmbr.ts_state)
        self.ended(True)
            
    def build_transaction(self):
        '''
        
        '''
        rc, msgs = self.buildTransaction()
        self.message('return_code', rc)
        for msg in msgs:
            self.message('messages', msg)
        self.message('transaction', pack(self._get_transaction_list()))
        self.ended(True)
        
    def _get_transaction_list(self):
        ''' 
        Generate a list of the current transaction to show in at TreeView
        based on YumOutput.listTransaction.
        used yum translation wrappers, so we can reuse the allready translated strings
        '''
        out_list = []
        sublist = []
        self.tsInfo.makelists()        
        for (action, pkglist) in [(yum.i18n._('Installing'), self.tsInfo.installed),
                            (yum_translated('Updating'), self.tsInfo.updated),
                            (yum_translated('Removing'), self.tsInfo.removed),
                            (yum_translated('Installing for dependencies'), self.tsInfo.depinstalled),
                            (yum_translated('Updating for dependencies'), self.tsInfo.depupdated),
                            (yum_translated('Removing for dependencies'), self.tsInfo.depremoved)]:
            for txmbr in pkglist:
                (n, a, e, v, r) = txmbr.pkgtup
                evr = txmbr.po.printVer()
                repoid = txmbr.repoid
                pkgsize = float(txmbr.po.size)
                size = format_number(pkgsize)
                alist = []
                for (obspo, relationship) in txmbr.relatedto:
                    if relationship == 'obsoletes':
                        appended = yum_translated('     replacing  %s%s%s.%s %s\n\n')
                        appended %= ("", obspo.name, "",
                                     obspo.arch, obspo.printVer())
                        alist.append(appended)
                el = (n, a, evr, repoid, size, alist)
                sublist.append(el)
            if pkglist:
                out_list.append([action, sublist])
                sublist = []
        for (action, pkglist) in [(yum_translated('Skipped (dependency problems)'),
                                   self.skipped_packages), ]:
            lines = []
            for po in pkglist:
                (n, a, e, v, r) = po.pkgtup
                evr = po.printVer()
                repoid = po.repoid
                pkgsize = float(po.size)
                size = format_number(pkgsize)
                el = (n, a, evr, repoid, size, alist)
                sublist.append(el)
            if pkglist:
                out_list.append([action, sublist])
                sublist = []
                
        return out_list        
        
                    
    def run_transaction(self):
        '''
        
        '''
        try:
            rpmDisplay = YumexRPMCallback(self)
            callback = YumexTransCallback(self)
            self.processTransaction(callback = callback, rpmDisplay = rpmDisplay)
            self.ended(True)
        except Errors.YumBaseError, e:
            self.error(_('Error in yum Transaction : %s') % str(e))
            self.ended(False)            
        except:    
            self.error("Exception in run_transaction")
            etype = sys.exc_info()[0]
            evalue = sys.exc_info()[1]
            self.error(str(etype) + ' : ' + str(evalue))
            self.ended(False)

    def _askForGPGKeyImport(self, po, userid, hexkeyid):
        ''' 
        Ask for GPGKeyImport 
        This need to be overloaded in a subclass to make GPG Key import work
        '''
        self.gpg_check(po, userid, hexkeyid)
        line = sys.stdin.readline().strip('\n')
        if line == ':true':
            return True
        else:
            return False

            
    
    def get_groups(self, args):
        '''
        get category/group list
        '''
        all_groups = []
        cats = self.comps.get_categories()
        for category in cats:
            cat = (category.categoryid, category.ui_name, category.ui_description)
            cat_grps = []
            grps = [self.comps.return_group(g) for g in category.groups if self.comps.has_group(g)]
            for grp in grps:
                icon = None
                fn = "/usr/share/pixmaps/comps/%s.png" % grp.groupid
                if os.access(fn, os.R_OK):
                    icon = fn
                else:
                    fn = "/usr/share/pixmaps/comps/%s.png" % category.categoryid
                    if os.access(fn, os.R_OK):
                        icon = fn

                elem = (grp.groupid, grp.ui_name, grp.ui_description, grp.installed, icon)
                cat_grps.append(elem)
            all_groups.append((cat, cat_grps))
        self.message('groups', pack(all_groups))
        self.ended(True)

    def get_group_packages(self, args):
        '''
        
        @param args:
        '''
        grpid = args[0]
        grp_flt = args[1]
        grp = self.comps.return_group(grpid)
        if grp:
            if grp_flt == 'all':
                best_pkgs = self._group_names2aipkgs(grp.packages)
            else:
                best_pkgs = self._group_names2aipkgs(grp.mandatory_packages.keys() + grp.default_packages.keys())
            for key in best_pkgs:
                (apkg, ipkg) = best_pkgs[key][0]
                if ipkg:
                    self._show_package(ipkg, 'r')
                else:
                    self._show_package(apkg, 'i')
            self.ended(True)
        else:
            self.ended(False)

    # Copied from yum (output.py), an ideal candidate to be implemented in yum base.
    def _group_names2aipkgs(self, pkg_names):
        """ Convert pkg_names to installed pkgs or available pkgs, return
            value is a dict on pkg.name returning (apkg, ipkg). """
        ipkgs = self.rpmdb.searchNames(pkg_names)
        apkgs = self.pkgSack.searchNames(pkg_names)
        apkgs = packagesNewestByNameArch(apkgs)

        # This is somewhat similar to doPackageLists()
        pkgs = {}
        for pkg in ipkgs:
            pkgs[(pkg.name, pkg.arch)] = (None, pkg)
        for pkg in apkgs:
            key = (pkg.name, pkg.arch)
            if key not in pkgs:
                pkgs[(pkg.name, pkg.arch)] = (pkg, None)
            elif pkg.verGT(pkgs[key][1]):
                pkgs[(pkg.name, pkg.arch)] = (pkg, pkgs[key][1])

        # Convert (pkg.name, pkg.arch) to pkg.name dict
        ret = {}
        for (apkg, ipkg) in pkgs.itervalues():
            pkg = apkg or ipkg
            ret.setdefault(pkg.name, []).append((apkg, ipkg))
        return ret
            

    def search(self, args):
        '''
        
        @param args:
        '''
        keys = unpack(args[0])
        filters = unpack(args[1])
        ygh = self.doPackageLists(pkgnarrow = 'updates')
        pkgs = {}
        for found in self.searchGenerator(filters, keys, showdups = True, keys = True):
            pkg = found[0]
            fkeys = found[1]
            if not len(fkeys) == len(keys): # skip the result if not all keys matches
                continue
            na = "%s.%s" % (pkg.name, pkg.arch)
            if not na in pkgs:
                pkgs[na] = [pkg]
            else:
                pkgs[na].append(pkg)
        for na in pkgs:
            best = packagesNewestByNameArch(pkgs[na])
            for po in best:           
                if self.rpmdb.contains(po = po): # if the best po is installed, then return the installed po 
                    (n, a, e, v, r) = po.pkgtup
                    po = self.rpmdb.searchNevra(name = n, arch = a, ver = v, rel = r, epoch = e)[0]
                    action = 'r'
                else:
                    if po in ygh.updates:
                        action = 'u'
                    else:
                        action = 'i'
                self._show_package(po, action)    
        self.ended(True)
    
    def get_repos(self, args):
        '''
        
        @param args:
        '''
        for repo in self.repos.repos:
            self._show_repo(self.repos.getRepo(repo))
        self.ended(True)
            
    
    def enable_repo(self, args):
        '''
        
        @param args:
        '''
        ident = args[0]
        state = (args[1] == 'True')
        self.debug("Repo : %s Enabled : %s" % (ident, state))
        repo = self.repos.getRepo(ident)
        if repo:
            if state:
                self.repos.enableRepo(ident)
            else:
                self.repos.disableRepo(ident)
            self._show_repo(repo)
        else:
            self.error("Repo : %s not found" % ident)

    def parse_command(self, cmd, args):
        ''' parse the incomming commands and do the actions '''
        if cmd == 'get-packages':       # get-packages <Package filter
            self.get_packages(args[0])
        elif cmd == 'get-attribute':
            self.get_attribute(args)
        elif cmd == 'get-changelog':
            self.get_changelog(args)
        elif cmd == 'add-transaction':
            self.add_transaction(args)
        elif cmd == 'remove-transaction':
            self.remove_transaction(args)
        elif cmd == 'list-transaction':
            self.list_transaction()
        elif cmd == 'run-transaction':
            self.run_transaction()
        elif cmd == 'build-transaction':
            self.build_transaction()
        elif cmd == 'get-groups':
            self.get_groups(args)
        elif cmd == 'get-group-packages':
            self.get_group_packages(args)
        elif cmd == 'get-repos':
            self.get_repos(args)
        elif cmd == 'enable-repo':
            self.enable_repo(args)
        elif cmd == 'search':
            self.search(args)
        else:
            self.error('Unknown command : %s' % cmd)

    def dispatcher(self):
        ''' receive commands and parameter from stdin (from the client) '''        
        try:
            while True:
                self.write(':ready')
                line = sys.stdin.readline().strip('\n')
                if not line or line.startswith('exit'):
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
                fn, lineno, func, codeline = tub # file,lineno, function, codeline
                errmsg += '  File : %s , line %s, in %s;' % (fn, str(lineno), func)
                errmsg += '    %s ;' % codeline
            self.write(":exception\t%s" % errmsg)
            self.ended(True)
        self.quit()

class YumexTransCallback:
    '''
    '''
    
    def __init__(self, base):
        '''
        
        @param base:
        '''
        self.base = base

    def event(self, state, data = None):
        '''
        
        @param state:
        @param data:
        '''

        if state == PT_DOWNLOAD:        # Start Downloading
            self.base.yum_state('download')
        elif state == PT_DOWNLOAD_PKGS:   # Packages to download
            self.base.dnlCallback.setPackages(data, 10, 30)
        elif state == PT_GPGCHECK:
            self.base.yum_state('gpg-check')
        elif state == PT_TEST_TRANS:
            self.base.yum_state('test-transaction')
        elif state == PT_TRANSACTION:
            self.base.yum_state('transaction')


class YumexRPMCallback(RPMBaseCallback):
    '''
    '''
    
    def __init__(self, base):
        '''
        
        @param base:
        '''
        RPMBaseCallback.__init__(self)
        self.base = base
        self._last_frac = 0.0
        self._last_pkg = None

    def event(self, package, action, te_current, te_total, ts_current, ts_total):
        '''
        
        @param package:
        @param action:
        @param te_current:
        @param te_total:
        @param ts_current:
        @param ts_total:
        '''
        # Handle rpm transaction progress
        try:
            if action != TS_UPDATED:
                if self._last_pkg != package:
                    self._last_pkg = package
                    self._last_frac = 0.0
                frac = float(te_current) / float(te_total)
                if frac > 0.994:
                    frac = 1.0
                if frac > self._last_frac + 0.005 or frac == 1.0:
                    #self.base.debug(str([self.action[action], str(package), frac, ts_current, ts_total]))
                    self.base.yum_rpm(self.action[action], str(package), frac, ts_current, ts_total)
                    self._last_frac = frac
            else:
                self.base.yum_rpm(self.action[action], str(package), 1.0, ts_current, ts_total)
                
        except:
            self.base.error('RPM Callback error : %s - %s ' % (self.action[action], str(package)))
            etype = sys.exc_info()[0]
            self.base.debug(str(etype))
        
    def scriptout(self, package, msgs):
        '''
        
        @param package:
        @param msgs:
        '''
        # Handle rpm scriptlet messages
        if msgs:
            self.base.yum_logger('RPM Scriptlet: %s' % msgs)

class YumexDownloadCallback(DownloadBaseCallback):
    """ Download callback handler """
    def __init__(self, base):
        '''
        
        @param base:
        '''
        DownloadBaseCallback.__init__(self)
        self.base = base
        self.percent_start = 0
        self.saved_pkgs = None
        self.number_packages = 0
        self.download_package_number = 0
        self.current_name = None
        self.current_type = None
        self._current_pkg = None
        self._printed =  []

    def setPackages(self, new_pkgs, percent_start, percent_length):
        '''
        
        @param new_pkgs:
        @param percent_start:
        @param percent_length:
        '''
        self._printed =  []
        self.saved_pkgs = new_pkgs
        self.number_packages = float(len(self.saved_pkgs))
        self.percent_start = percent_start

    def _getPackage(self, name):
        '''
        
        @param name:
        '''
        if self.saved_pkgs:
            for pkg in self.saved_pkgs:
                if isinstance(pkg, YumLocalPackage):
                    rpmfn = pkg.localPkg
                else:
                    rpmfn = os.path.basename(pkg.remote_path) # get the rpm filename of the package
                if rpmfn == name:
                    return pkg
        return None
        
    def updateProgress(self, name, frac, fread, ftime):
        '''
         Update the progressbar (Overload in child class)
        @param name: filename
        @param frac: Progress fracment (0 -> 1)
        @param fread: formated string containing BytesRead
        @param ftime: formated string containing remaining or elapsed time
        '''

        val = int(frac * 100)

        # new package
        if val == 0:
            if ':' in name:
                cnt, fn = name.split(':')
                name = fn.strip()
                cur, tot = cnt[1: - 1].split('/') 
            pkg = self._getPackage(name)
            self._current_pkg = pkg
            if pkg: # show package to download
                self.current_name = str(pkg)
                self.current_type = 'PKG'
            elif name.endswith('.drpm'): # Presto delta rpm
                self.current_name = name
                self.current_type = 'PKG'                
            elif not name.endswith('.rpm'):
                self.current_name = name
                self.current_type = 'REPO'
            else:
                self.current_name = name
                self.current_type = 'PKG'
                

        self.base.yum_dnl(self.current_type, self.current_name, val)

        # keep track of how many we downloaded
        if val == 100:
            self.download_package_number += 1
            self.current_name = None
            if name not in self._printed:
                # show downloaded <filename> ( <size> )
                self.base.info(_('Downloaded : %s ( %s )') %(name,self.totSize))
                self._printed.append(name)

if __name__ == "__main__":
    pass
