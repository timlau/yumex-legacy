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
import types
import time

from yum.packageSack import packagesNewestByNameArch
from yum.update_md import UpdateMetadata

from yumexbase.constants import *
from yumexbackend import YumHistoryTransaction, YumHistoryPackage, pack, unpack
from yumexbase import YumexBackendFatalError


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
from urlgrabber.grabber import URLGrabber, URLGrabError

from yum.i18n import _ as yum_translated

# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
import logging
from yumexbase.i18n import _, P_
# pylint: enable-msg=W0611

def catchYumException(func):
    """
    This decorator catch yum exceptions and send fatal signal to frontend 
    """
    def newFunc(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Errors.RepoError, e:
            base = args[0]
            # signal to the front end that we have a fatal error
            base.fatal('repo-error', str(e))
            base.ended(False)

    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

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
        get-packages <pkg-filter> <show_dupes>  : get a list of packages based on a filter
        get-packages-size                    : 
        get-packages-repo                    : 
        get-attribute <pkg_id> <attribute>   : get an attribute of an package
        get-changelog                        : 
        update-info                          : 
        set-option                           : 
        add-transaction <pkg_id> <action>    : add a po to the transaction
        remove-transaction <pkg_id>          : add a po to the transaction
        list-transaction                     : list po's in transaction
        build-transaction                    : build the transaction (resolve dependencies)
        run-transaction                      : run the transaction
        get-groups                           : Get the groups
        get-group-packages                   : 
        get-repos                            : Get the repositories
        enable-repo                          : enable/disable a repository
        enable-repo-persistent               : 
        search                               : search
        clean                                : 
        get-history                          : 
        get-history-packages                 : 
        history-undo                         : 
        history-redo                         : 
    
        Parameters:
        <pkg-filter> : all,installed,available,updates,obsoletes
        <pkg_id>     : name epoch ver release arch repoid ('\t' separated)
        <attribute>  : pkg attribute (ex. description, changelog)
        <action>     : 'install', 'update', 'remove' 
        <show_dupes> : Show duplicate packages (True or False)
        
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
        :media-change <media info> 
        
        Parameters:
        <message>  : a text message ('\n' is replaced with ';'
        <pkg>      : name epoch ver release arch repoid summary ('\t' separated)
        <object>   : an package attribute pickled and base64 encoded.
      
    
    """

    def __init__(self, debuglevel=2, plugins=True, offline=False, enabled_repos=None, yum_conf='/etc/yum.conf'):
        '''  Setup the spawned server '''
        yum.YumBase.__init__(self)
        self.mediagrabber = self.mediaGrabber
        parser = OptionParser()
        # Setup yum preconfig options
        self.preconf.debuglevel = debuglevel
        self.preconf.init_plugins = plugins
        self.preconf.optparser = parser
        if yum_conf != '/etc/yum.conf':
            self.info(_('Using %s for yum configuration') % yum_conf)
        self.preconf.fn = yum_conf
        # Disable refresh-package plugin, it will get in the way every time we finish a transaction
        self.preconf.disabled_plugins = ['refresh-packagekit']
        logginglevels.setLoggingApp('yumex')
        if hasattr(self, 'run_with_package_names'):
            self.run_with_package_names.add("yumex")
        self.doLock()
        self.dnlCallback = YumexDownloadCallback(self)
        self.repos.setProgressBar(self.dnlCallback)
        # make some dummy options,args for yum plugins
        (options, args) = parser.parse_args()
        self.plugins.setCmdLine(options, args)
        dscb = DepSolveProgressCallBack(ayum=self)
        self.dsCallback = dscb
        self.offline = offline
        # Setup repos
        self._setup_repos(enabled_repos)
        # Setup failure callback
        freport = (self._failureReport, (), {})
        self.repos.setFailureCallback(freport)
        self._updateMetadata = None # Update metadata cache 
        self._updates_list = None
        self.write(':started') # Let the front end know that we are up and running

    def _is_local_repo(self, repo):
        '''
        Check if an repo is local (media or file:// repo)
        '''
        if repo.mediaid or self._is_file_url(repo.baseurl):
            return True
        else:
            return False

    def _is_file_url(self, urls):
        return [url for url in urls if url.startswith('file:')]

    def _setup_repos(self, enabled_repos):
        '''
        Setup the repo to be enabled/disabled
        '''
        if not self.offline: # Online
            if enabled_repos: # Use the positive list of repos to enable
                for repo in self.repos.repos.values():
                    if repo.id in enabled_repos: # is in the positive list
                        self.repos.enableRepo(repo.id)
                    else:
                        self.repos.disableRepo(repo.id)
        else: # Offline, use only media or locale file:// repos
            if enabled_repos: # Use the supplied list of repos to enable
                for repo in self.repos.repos.values():
                    if repo.id in enabled_repos:
                        if self._is_local_repo(repo): # is local ?
                            self.repos.enableRepo(repo.id)
                        else: # Not local disable it
                            self.info(_("No network connection, disable non local repo %s") % repo.id)
                            self.repos.disableRepo(repo.id)
                    else: # not in positive list, disable it
                        self.repos.disableRepo(repo.id)
            else: # Use the default enabled ones
                for repo in self.repos.listEnabled():
                    if self._is_local_repo(repo): # is local ?
                        self.repos.enableRepo(repo.id)
                    else: # No, disable it
                        self.info(_("No network connection, disable non local repo %s") % repo.id)
                        self.repos.disableRepo(repo.id)

    def doLock(self, lockfile=YUM_PID_FILE):
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

    def mediaGrabber(self, *args, **kwargs):
        '''
        Media handler
        '''
        mediaid = kwargs["mediaid"]
        discnum = kwargs["discnum"]
        name = kwargs["name"]
        found = False
        prompt_first = False # check without asking the user
        while(not found):
            mp = self._ask_for_media_change(prompt_first, mediaid, name, discnum)
            # We got the media mount point
            if mp:
                # the actual copying is done by URLGrabber
                ug = URLGrabber(checkfunc=kwargs["checkfunc"])
                try:
                    ug.urlgrab("%s/%s" % (mp, kwargs["relative"]),
                        kwargs["local"], text=kwargs["text"],
                        range=kwargs["range"], copy_local=1)
                except (IOError, URLGrabError):
                    # ask again as user might got a better media or he might clean the media
                    prompt_first = True # next time prompt user first so he can cancel
                else:
                    found = True # done
            else:
                # mp==None ie. user canceled media change
                break
        if not found:
            # yumRepo will catch this
            raise yum.Errors.MediaError, _("The disc was not inserted")
        return kwargs["local"]

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
            if line[ -1] != '\n':
                continue
            data = line[:-1].split(':\t', 1)
            if data[1].endswith(' kB'):
                data[1] = data[1][:-3]
            ps[data[0].strip().lower()] = data[1].strip()
        return ps

    def quit(self):
        '''
        Exit the yum backend
        '''
        self.info(_("Closing rpm db and releasing yum lock  "))
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

    def _is_installed(self, po):
        '''
        Check if a package is installed
        @param po: package to check for 
        '''
        (n, a, e, v, r) = po.pkgtup
        po = self.rpmdb.searchNevra(name=n, arch=a, ver=v, rel=r, epoch=e)
        if po:
            return True
        else:
            return False


    def _show_history_package(self, pkg):
        ''' write history package result'''
        if not hasattr(pkg, 'state_installed'):
            pkg.state_installed = self._is_installed(pkg)
        yhp = pack(YumHistoryPackage(pkg))
        self.write(":histpkg\t%s" % yhp)

    def _show_history_item(self, yht):
        ''' write package result'''
        item = pack(YumHistoryTransaction(yht))
        self.write(":hist\t%s" % item)

    def _show_package(self, pkg, action=None):
        ''' write history package result'''
        summary = pack(pkg.summary)
        recent = self._get_recent(pkg)
        action = pack(action)
        self.write(":pkg\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" %
                   (pkg.name, pkg.epoch, pkg.ver, pkg.rel, pkg.arch, pkg.ui_from_repo,
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

    def debug(self, msg, name=None):
        ''' write an debug message '''
        if not name:
            classname = __name__.split('.')[-1]
            name = classname + "." + sys._getframe(1).f_code.co_name
        self.write(":debug\t%s\t%s" % (msg, name))

    def warning(self, msg):
        ''' write an warning message '''
        self.write(":warning\t%s" % msg)

    def fatal(self, err, msg):
        ''' write an fatal message '''
        pmsg = pack(msg)
        self.write(":fatal\t%s\t%s" % (err, pmsg))
        raise YumexBackendFatalError(err, msg)

    def gpg_check(self, po, userid, hexkeyid):
        ''' write an fatal message '''
        value = (str(po), userid, hexkeyid)
        value = pack(value)
        self.write(":gpg-check\t%s" % (value))

    def media_change(self, prompt_first, media_id, media_name, media_num):
        ''' write an media change message '''
        value = (prompt_first, media_id, media_name, media_num)
        value = pack(value)
        self.write(":media-change\t%s" % (value))


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

    def yum_dnl(self, ftype, name, percent, cur, tot, fread, ftotal, ftime):
        '''
        send an yum download progress message to the frontend
        @param ftype: filetype ('PKG' or 'REPO')
        @param name: filename
        @param percent: percent complette
        @param cur: current number of file being downloaded
        @param tot: total number of files to download
        @param fread: formatted number of bytes read
        @param ftime: formatted ETA
        '''
        value = (ftype, name, percent, cur, tot, fread, ftotal, ftime)
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


    @catchYumException
    def get_packages(self, narrow, dupes):
        '''
        get list of packages and send results 
        @param narrow:
        '''
        if narrow:
            show_dupes = (dupes == 'True')
            self.info(PACKAGE_LOAD_MSG[narrow])
            ygh = self.doPackageLists(pkgnarrow=narrow, showdups=show_dupes)
            if narrow == "all":
                updates = ygh.updates
                obsoletes = ygh.obsoletes
                for pkg in ygh.installed:
                    self._show_package(pkg, 'r')
                for pkg in ygh.available:
                    if pkg in updates:
                        action = 'u'
                    elif pkg in obsoletes:
                        action = 'o'
                    else:
                        action = 'i'
                    self._show_package(pkg, action)
            else:
                action = const.FILTER_ACTIONS[narrow]
                for pkg in getattr(ygh, narrow):
                    self._show_package(pkg, action)
        self.ended(True)

    def get_packages_size(self, ndx):
        '''
        get list of packages in a size range
        @param ndx: Size range index
        '''
        ygh = self.doPackageLists()
        action = const.FILTER_ACTIONS['available']
        for pkg in ygh.available:
            if self._in_size_range(pkg, ndx):
                self._show_package(pkg, action)
        action = const.FILTER_ACTIONS['installed']
        for pkg in ygh.installed:
            if self._in_size_range(pkg, ndx):
                self._show_package(pkg, action)
        del ygh
        self.ended(True)

    def _in_size_range(self, pkg, ndx):
        min, max = SIZE_RANGES[ndx]
        if pkg.size >= min and pkg.size < max:
            return True
        else:
            return False

    def get_packages_repo(self, repoid):
        '''
        get list of packages in a size range
        @param ndx: Size range index
        '''
        ygh = self.doPackageLists()
        action = const.FILTER_ACTIONS['available']
        for pkg in ygh.available:
            if self._in_a_repo(pkg, repoid):
                self._show_package(pkg, action)
        action = const.FILTER_ACTIONS['installed']
        for pkg in ygh.installed:
            if self._in_a_repo(pkg, repoid, inst=True):
                self._show_package(pkg, action)
        del ygh
        self.ended(True)

    def _in_a_repo(self, pkg, repoid, inst=False):
        if not inst and pkg.repoid == repoid:
            return True
        elif hasattr(pkg, 'yumdb_info') and hasattr(pkg.yumdb_info, 'from_repo'):
            if pkg.yumdb_info.from_repo == repoid:
                return True
            else:
                return False
        else:
            return False

    def _getPackage(self, para):
        ''' find the real package from an package id'''
        n, e, v, r, a, ident = para
        if ident == 'installed' or ident.startswith('@'):
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
        pkgstr = args[:-1]
        attr = args[ -1]
        po = self._getPackage(pkgstr)
        res = pack(None)
        if po:
            res = getattr(po, attr)
            res = pack(res)
        self.write(':attr\t%s' % res)

    def get_changelog(self, args):
        ''' get a given number of changelog lines '''
        pkgstr = args[:-1]
        num = int(args[ -1])
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
        pkgstr = args[:-1]
        action = args[ -1]
        po = self._getPackage(pkgstr)
        txmbrs = []
        if action == "install":
            txmbrs = self.install(po)
        elif action == "update" or action == "obsolete":
            txmbrs = self.update(po)
        elif action == "remove":
            txmbrs = self.remove(po)
        elif action == "reinstall":
            txmbrs = self.reinstall(po)
        elif action == "downgrade":
            txmbrs = self.downgrade(po)
        for txmbr in txmbrs:
            self._show_package(txmbr.po, txmbr.ts_state)
            self.debug("Added : " + str(txmbr), __name__)
        self.ended(True)

    def remove_transaction(self, args):
        '''
        
        @param args:
        '''
        pkgstr = args
        po = self._getPackage(pkgstr)
        self.tsInfo.remove(po)

    def reset_transaction(self):
        '''
        reset tsInfo for a new run
        '''
        self._tsInfo = None


    def list_transaction(self):
        '''
        
        '''
        for txmbr in self.tsInfo:
            self._show_package(txmbr.po, txmbr.ts_state)
        self.ended(True)

    def _show_packages_in_transaction(self, action):
        '''
        
        '''
        for txmbr in self.tsInfo:
            self._show_package(txmbr.po, action)
        self.ended(True)

    def run_command(self, cmd, userlist):
        self.reset_transaction()
        cmd = cmd[:2]
        try:
            if cmd == 'in':
                action = 'i'
                for pat in userlist:
                    self.install(pattern=pat)
            elif cmd == 're' or cmd == 'er':
                action = 'r'
                for pat in userlist:
                    self.remove(pattern=pat)
        except Errors.InstallError, e:
            pass
        self._show_packages_in_transaction(action)
        self.reset_transaction()


    def build_transaction(self):
        '''
        
        '''
        rc, msgs = self.buildTransaction()
        self.message('return_code', rc)
        for msg in msgs:
            self.message('messages', msg)
        self.message('transaction', pack(self._get_transaction_list()))
        self.message("size", self._get_download_size())
        self.ended(True)

    def _get_download_size(self):
        total = 0L
        dlpkgs = [x.po for x in self.tsInfo.getMembers() if x.ts_state in ("i", "u")]
        for po in dlpkgs:
            total += po.size
        return format_number(total)

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
            self.processTransaction(callback=callback, rpmDisplay=rpmDisplay)
            self.ended(True)
        except Errors.YumBaseError, e:
            self.error(_('Error in yum Transaction : %s') % str(e))
            self.ended(False)
        except:
            self.error(_("Exception in run_transaction"))
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

    def _ask_for_media_change(self, prompt_first, media_id, media_name, media_num=None):
        ''' 
        Ask for media change 
        '''
        if media_num:
            self.debug("media : %s #%d is needed" % (media_name, media_num), __name__)
        else:
            self.debug("media : %s is needed" % (media_name,), __name__)
        self.media_change(prompt_first, media_id, media_name, media_num)
        line = sys.stdin.readline().strip('\n')
        if line.startswith(':mountpoint'):
            mountpoint = unpack(line.split('\t')[1])
            self.debug("media mount point : %s" % mountpoint, __name__)
            return mountpoint
        else:
            self.debug("no media mount point returned", __name__)
            return None

    def _failureReport(self, errobj):
        """failure output for failovers from urlgrabber"""

        self.warning(_('Failure getting %s: ') % errobj.url)
        self.warning(_('Trying other mirror.'))
        raise errobj.exception

    def _interrupt_callback(self, cbobj):
        '''Handle CTRL-C's during downloads

        If a CTRL-C occurs a URLGrabError will be raised to push the download
        onto the next mirror.  
        
        @param cbobj: urlgrabber callback obj
        '''
        # Go to next mirror
        raise URLGrabError(15, 'user interrupt')


    def get_groups(self, args):
        '''
        get category/group list
        '''
        all_groups = []
        try:
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
                cat_grps.sort()
                all_groups.append((cat, cat_grps))
        except Errors.GroupsError, e:
            print str(e)
        all_groups.sort()
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

    def _get_updates(self):
        if not self._updates_list:
            ygh = self.doPackageLists(pkgnarrow='updates')
            self._updates_list = ygh.updates
        return self._updates_list

    def _return_packages(self, pkgs):
        updates = self._get_updates()
        for po in pkgs:
            if self.rpmdb.contains(po=po): # if the best po is installed, then return the installed po 
                (n, a, e, v, r) = po.pkgtup
                po = self.rpmdb.searchNevra(name=n, arch=a, ver=v, rel=r, epoch=e)[0]
                action = 'r'
            else:
                if po in updates:
                    action = 'u'
                else:
                    action = 'i'
            self._show_package(po, action)


    def search_prefix(self, prefix):
        prefix += '*'
        self.debug("prefix: %s " % prefix)
        pkgs = self.pkgSack.returnPackages(patterns=[prefix])
        best = packagesNewestByNameArch(pkgs)
        self._return_packages(best)
        self.ended(True)

    def search(self, args):
        '''
        
        @param args:
        '''
        keys = unpack(args[0])
        filters = unpack(args[1])
        ygh = self.doPackageLists(pkgnarrow='updates')
        pkgs = {}
        for found in self.searchGenerator(filters, keys, showdups=True, keys=True):
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
            self._return_packages(best)
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
        self.debug("Repo : %s Enabled : %s" % (ident, state), __name__)
        repo = self.repos.getRepo(ident)
        if repo:
            if state:
                self.repos.enableRepo(ident)
            else:
                self.repos.disableRepo(ident)
            self._show_repo(repo)
        else:
            self.error("Repo : %s not found" % ident)

    def enable_repo_persistent(self, args):
        '''
        
        @param args:
        '''
        ident = args[0]
        state = (args[1] == 'True')
        repo = self.repos.getRepo(ident)
        if repo:
            if state:
                repo.enablePersistent()
                self.info(_("The %s repository has been enabled permanently") % ident)
            else:
                repo.disablePersistent()
                self.info(_("The %s repository has been disabled permanently") % ident)
        else:
            self.error("Repo : %s not found" % ident)
        self.ended(True)

    def set_option(self, args):
        option = args[0]
        value = unpack(args[1])
        on_repos = unpack(args[2])
        if hasattr(self.conf, option):
            setattr(self.conf, option, value)
            self.info(_("Setting Yum Option %s = %s") % (option, value))
            for repo in self.repos.repos.values():
                if repo.isEnabled():
                    if hasattr(repo, option):
                        setattr(repo, option, value)
                        self.debug("Setting Yum Option %s = %s (%s)" % (option, value, repo.id), __name__)

        self.ended(True)

    @property
    def update_metadata(self):
        if not self._updateMetadata:
            self._updateMetadata = UpdateMetadata()
            for repo in self.repos.listEnabled():
                try:
                    self._updateMetadata.add(repo)
                except:
                    pass # No updateinfo.xml.gz in repo
        return self._updateMetadata

    def get_update_info(self, args):
        '''
        Get update infomation
        '''
        pkg = self._getPackage(args)
        if pkg:
            md = self.update_metadata
            nvr = (pkg.name, pkg.ver, pkg.rel)
            notices = md.get_notices(pkg.name)
            for ret in notices:
                self.message("updateinfo", ret)
                po = self._get_updated_po(pkg)
                self.message("updated_po", str(po))
        self.ended(True)

    def _get_updated_po(self, pkg):
        po = None
        tuples = self._getUpdates().getUpdatesTuples(name=pkg.name)
        if not tuples:
            tuples = self._getUpdates().getObsoletersTuples(name=pkg.name)
        if tuples:
            tup = tuples[0]
            if tup:
                new, old = tup
                po = self.getInstalledPackageObject(old)
        return po

    def clean(self, args):
        what = args[0]
        if what == 'metadata':
            self.cleanMetadata()
            msg = _("Cleaned metadata from local cache")
        elif what == 'dbcache':
            self.cleanSqlite()
            msg = _("Cleaned dbcache")
        elif what == 'packages':
            self.cleanPackages()
            msg = _("Cleaned packages from local cache")
        elif what == 'all':
            msg = _("Cleaned everything from local cache")
            self.cleanMetadata()
            self.cleanPackages()
            self.cleanSqlite()
        self.info(msg)
        self.ended(True)

    def search_history(self, pattern):
        """
        Get the yum history elements
        """
        if hasattr(self, "_history"): # Yum supports history
            tids = self.history.search(pattern)
            yhts = self.history.old(tids)
            for yht in yhts:
                self._show_history_item(yht)
            self.ended(True)
        else:
            self.ended(False)

    def get_history(self, args):
        """
        Get the yum history elements
        """
        if hasattr(self, "_history"): # Yum supports history
            yhts = self.history.old()
            for yht in yhts:
                self._show_history_item(yht)
            self.ended(True)
        else:
            self.ended(False)

    def get_history_packages(self, tid, data_set='trans_data'):
        tids = self.history.old([tid])
        for yht in tids:
            yhp = getattr(yht, data_set)
            for pkg in yhp:
                self._show_history_package(pkg)
        self.ended(True)

    def history_undo(self, args):
        '''
        Undo a history transaction
        '''
        tid = int(args[0])
        tids = self.history.old([tid])
        if tids:
            yum.YumBase.history_undo(self, tids[0])
        print "Transaction after undo"
        for txmbr in self.tsInfo:
            print txmbr.po
        if len(self.tsInfo) > 0:
            self.ended(True)
        else:
            self.ended(False)

    def history_redo(self, args):
        '''
        Redo a history transaction
        '''
        tid = int(args[0])
        tids = self.history.old([tid])
        if tids:
            yum.YumBase.history_redo(self, tids[0])
        if len(self.tsInfo) > 0:
            self.ended(True)
        else:
            self.ended(False)

    def parse_command(self, cmd, args):
        ''' parse the incomming commands and do the actions '''
        if cmd == 'get-packages':       # get-packages <Package filter
            self.get_packages(args[0], args[1])
        elif cmd == 'get-attribute':
            self.get_attribute(args)
        elif cmd == 'get-changelog':
            self.get_changelog(args)
        elif cmd == 'add-transaction':
            self.add_transaction(args)
        elif cmd == 'remove-transaction':
            self.remove_transaction(args)
        elif cmd == 'reset-transaction':
            self.reset_transaction()
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
        elif cmd == 'get-packages-size':
            self.get_packages_size(args[0])
        elif cmd == 'get-packages-repo':
            self.get_packages_repo(args[0])
        elif cmd == 'get-repos':
            self.get_repos(args)
        elif cmd == 'enable-repo':
            self.enable_repo(args)
        elif cmd == 'enable-repo-persistent':
            self.enable_repo_persistent(args)
        elif cmd == 'search':
            self.search(args)
        elif cmd == 'search-prefix':
            self.search_prefix(args[0])
        elif cmd == 'update-info':
            self.get_update_info(args)
        elif cmd == 'set-option':
            self.set_option(args)
        elif cmd == 'clean':
            self.clean(args)
        elif cmd == 'get-history':
            self.get_history(args)
        elif cmd == 'get-history-packages':
            self.get_history_packages(args[0], args[1])
        elif cmd == 'history-undo':
            self.history_undo(args)
        elif cmd == 'history-redo':
            self.history_redo(args)
        elif cmd == 'search-history':
            self.search_history(unpack(args[0]))
        elif cmd == 'run-command':
            self.run_command(args[0], unpack(args[1]))
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
                ts = time.time()
                self.parse_command(args[0], args[1:])
                t = time.time() - ts
                self.debug("%s Args: %s  took %.2f s to complete" % (args[0], args[1:], t), __name__)
        except YumexBackendFatalError, e:
            self.ended(True)
            self.quit()
        except:
            errmsg = traceback.format_exc()
            #print errmsg
            self.write(":exception\t%s" % pack(errmsg))
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

    def event(self, state, data=None):
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
        self._printed = {}

    # Copied from yum/output.py        
    def pkgname_ui(self, pkgname, ts_states=None):
        """ Get more information on a simple pkgname, if we can. We need to search
            packages that we are dealing with atm. and installed packages (if the
            transaction isn't complete). """

        if ts_states is None:
            #  Note 'd' is a placeholder for downgrade, and
            # 'r' is a placeholder for reinstall. Neither exist atm.
            ts_states = ('d', 'e', 'i', 'r', 'u')

        matches = []
        def _cond_add(po):
            if matches and matches[0].arch == po.arch and matches[0].verEQ(po):
                return
            matches.append(po)

        for txmbr in self.base.tsInfo.matchNaevr(name=pkgname):
            if txmbr.ts_state not in ts_states:
                continue
            _cond_add(txmbr.po)

        if not matches:
            return pkgname
        fmatch = matches.pop(0)
        if not matches:
            return str(fmatch)

        show_ver = True
        show_arch = True
        for match in matches:
            if not fmatch.verEQ(match):
                show_ver = False
            if fmatch.arch != match.arch:
                show_arch = False

        if show_ver: # Multilib. *sigh*
            if fmatch.epoch == '0':
                return '%s-%s-%s' % (fmatch.name, fmatch.version, fmatch.release)
            else:
                return '%s:%s-%s-%s' % (fmatch.epoch, fmatch.name,
                                        fmatch.version, fmatch.release)

        if show_arch:
            return '%s.%s' % (fmatch.name, fmatch.arch)

        return pkgname


    def event(self, package, action, te_current, te_total, ts_current, ts_total):
        '''g
        RPM Event callback handler
        @param package:
        @param action:
        @param te_current:
        @param te_total:
        @param ts_current:
        @param ts_total:
        '''
        # Handle rpm transaction progress
        try:
            # get the package name, if a string then get info from transaction
            if type(package) not in types.StringTypes:
                pkgname = str(package)
            else:
                pkgname = self.pkgname_ui(package)

            if action in (TS_UPDATE, TS_INSTALL, TS_TRUEINSTALL): # only show progress when something is installed
                if self._last_pkg != package:
                    self._last_pkg = package
                    self._last_frac = 0.0
                frac = float(te_current) / float(te_total)
                if frac > 0.994:
                    frac = 1.0
                if frac > self._last_frac + 0.005 or frac == 1.0:
                    #self.base.debug(str([self.action[action], str(package), frac, ts_current, ts_total]))
                    self.base.yum_rpm(self.action[action], pkgname, frac, ts_current, ts_total)
                    self._last_frac = frac
                    if frac == 1.0:
                        self.show_action(pkgname, action)
            else:
                self.base.yum_rpm(self.action[action], pkgname, 1.0, ts_current, ts_total)
                self.show_action(pkgname, action)


        except:
            self.base.error('RPM Callback error : %s - %s ' % (self.action[action], str(package)))
            errmsg = traceback.format_exc()
            for eline in errmsg.split('\n'):
                if eline:
                    self.base.error(eline)

    def show_action(self, package, action):
        '''
        Show action messages after trasaction is completted
        @param package: package name
        @param action: TS Action enum
        '''
        if not str(package) in self._printed:
            self._printed[str(package)] = 1
            self.base.info(RPM_ACTIONS[action] % (package))


    def scriptout(self, package, msgs):
        '''
        
        @param package:
        @param msgs:
        '''
        # Handle rpm scriptlet messages
        if msgs:
            self.base.info('RPM Scriptlet: %s' % msgs)

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
        self._printed = []
        self._cur = 1
        self._tot = 1

    def setPackages(self, new_pkgs, percent_start, percent_length):
        '''
        
        @param new_pkgs:
        @param percent_start:
        @param percent_length:
        '''
        self._printed = []
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
            self._cur = 1
            self._tot = 1
            if ':' in name:
                cnt, fn = name.split(':')
                name = fn.strip()
                cur, tot = cnt[1:-1].split('/')
                self._cur = cur
                self._tot = tot
            pkg = self._getPackage(name)
            self._current_pkg = pkg
            if pkg: # show package to download
                self.current_name = str(pkg)
                self.current_type = 'PKG'
            elif name == '<delta rebuild>': # Presto rebuilding rpm
                self.current_name = self.text
                self.current_type = 'REBUILD'
            elif name.endswith('.drpm'): # Presto delta rpm
                self.current_name = name
                self.current_type = 'PKG'
            elif not name.endswith('.rpm'):
                self.current_name = name
                self.current_type = 'REPO'
            else:
                self.current_name = name
                self.current_type = 'PKG'


        self.base.yum_dnl(self.current_type, self.current_name, val, self._cur, self._tot, fread, self.totSize, ftime)

        # keep track of how many we downloaded
        if val == 100:
            self.download_package_number += 1
            self.current_name = None
            if name not in self._printed:
                # show downloaded <filename> ( <size> )
                if name == '<delta rebuild>':
                    self.base.info(_('Rebuild from deltarpms completted'))
                else:
                    self.base.info(_('Downloaded : %s ( %s )') % (name, self.totSize))
                self._printed.append(name)




if __name__ == "__main__":
    pass
