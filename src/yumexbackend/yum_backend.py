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

'''
'''

# Imports

from yumexbase.constants import *
#from yumexbase import TimeFunction
from yum.misc import prco_tuple_to_string

from yumexbackend import YumexBackendBase, YumexTransactionBase
from yumexbackend.yum_client import YumClient, unpack
from yumexgui.dialogs import ErrorDialog, questionDialog, okCancelDialog
from yumexbackend.yumMediaManagerUDisks import MediaManagerUDisks as MediaManager
# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
from yumexbase import _, P_  # lint:ok
# pylint: enable-msg=W0611

class PackageCache:
    '''
    Package cache to contain packages from backend, so we dont have get them more
    than once.
    '''

    def __init__(self, backend, frontend):
        '''
        setup the cache
        @param backend:    backend instance
        '''
        for filter in ACTIONS_FILTER.values():
            setattr(self, filter, set())
        self._populated = []
        self._index = {}
        self.backend = backend
        self.frontend = frontend

    def reset(self):
        '''
        reset the cache
        '''
        for filter in ACTIONS_FILTER.values():
            setattr(self, filter, set())
        self._populated = []
        self._index = {}

    def _get_packages(self, pkg_filter):
        '''
        get a list of packages from the cache
        @param pkg_filter: the type of packages to get
        '''
        return list(getattr(self, str(pkg_filter)))

    def is_populated(self, pkg_filter):
        return str(pkg_filter) in self._populated

    def populate(self, pkg_filter, pkgs):
        '''
        '''
        self.find_packages(pkgs)
        self._populated.append(str(pkg_filter))


    def _add(self, po):
        if str(po) in self._index: # package is in cache
            return self._index[str(po)]
        else:
            target = getattr(self, ACTIONS_FILTER[po.action])
            self._index[str(po)] = po
            target.add(po)
            return po

    #@TimeFunction
    def find_packages(self, packages):
        pkgs = []
        i = 0
        for po in packages:
            i += 1
            if (i % 500) == 0: # Refresh gui + progressbar
                self.frontend.refresh()
            pkgs.append(self._add(po))
        return pkgs




class YumexBackendYum(YumexBackendBase, YumClient):
    ''' Yumex Backend Yume class

    This is the base class to interact with yum
    '''

    def __init__(self, frontend):
        '''

        @param frontend:
        '''
        transaction = YumexTransactionYum(self, frontend)
        YumexBackendBase.__init__(self, frontend, transaction)
        YumClient.__init__(self, frontend)
        self.dont_abort = False
        self.package_cache = PackageCache(self, frontend)

    # Overload the YumClient message methods

    def error(self, msg):
        """ error message """
        self.frontend.error(msg)

    def warning(self, msg):
        """ warning message """
        self.frontend.warning(msg)

    def info(self, msg):
        """ info message """
        self.frontend.info(msg)

    def exitcode(self, code):
        """ Exitcode from backend"""
        self.frontend.exitcode(code)


    def debug(self, msg, name=None):
        """ debug message """
        if not name:
            classname = __name__.split('.')[-1]
            name = classname + "." + sys._getframe(1).f_code.co_name
        self.frontend.debug(msg, name)

    def yum_logger(self, msg):
        """ yum logger message """
        if len(msg.strip()) > 0:
            # skip the bogus gtk error
            if 'gdk_x11_atom_to_xatom_for_display' in msg:
                return
            self.frontend.info("YUM: " + msg)

    def yum_rpm_progress(self, action, package, frac, ts_current, ts_total):
        """ yum rpm action progress handler """
        progress = self.frontend.get_progress()
        progress.set_action("%s %s" % (action, package))
        progress.set_fraction(frac, "%3i %%" % int(frac * 100))
        width = len("%s" % ts_total)
        progress.tasks.set_extra_label('run-trans', "<b>( %*s / %*s )</b>" % (width, ts_current, width, ts_total))

    def yum_dnl_progress(self, ftype, name, percent, cur, tot, fread, ftotal, ftime):
        """ yum download progress handler """
        progress = self.frontend.get_progress()
        if not progress.is_active(): # if the progress is hidden, then show it at set the labels.
            progress.set_title(_('Getting Package Information'))
            progress.set_header(_('Getting Package Information'))
            progress.show()
        if progress.tasks.current_running == 'download':
            width = len("%s" % tot)
            progress.tasks.set_extra_label('download', "<b>( %*s / %*s )</b>" % (width, cur, width, tot))
        progress.set_fraction(float(percent) / 100.0, "%3i %% ( %s / %s ) - %s" % (percent, fread, ftotal, ftime))
        #self.frontend.debug("Progress: %s - %s - %s - %s - %s" %  (cur, tot, fread, ftotal, ftime))
        if ftype == "REPO": # This is repo metadata being downloaded
            if percent > 0: # only show update labels once.
                return
            if '/' in name:
                values = name.split('/')
                repo, mdtype = values[0],values[-1] # there can be more than 2 values, take first & last
            else:
                repo = None
                mdtype = name
            msg = _("Unknown Repo Metadata type (%s) for %s") % (mdtype, '%s')
            for key in REPO_INFO_MAP:
                if key in mdtype:
                    msg = REPO_INFO_MAP[key]
                    break
            if repo:
                markup = "<b>%s</b>" % repo
                self.debug(msg % repo)
                progress.set_action(msg % markup)

            else:
                self.debug(msg)
                progress.set_action(msg)
        elif ftype == 'REBUILD':
            progress.set_action(_('Building rpms from deltarpm'))
        else: # this is a package being downloaded
            #self.frontend.debug("DNL (%s): %s - %3i %%" % (ftype,name,percent))
            if name:
                progress.set_action(name)
            else:
                self.frontend.debug("DNL (%s): %s - %3i %%" % (ftype, name, percent))


    def yum_state(self, state):
        '''

        @param state:
        '''
        progress = self.frontend.get_progress()
        if state == 'download':
            progress.set_header(_("Downloading Packages"))
            progress.tasks.next()
            progress.set_pulse(False)
        elif state == 'gpg-check':
            progress.set_pulse(True)
            progress.show_cancel(False) # Don't allow Cancel any more
            progress.set_header(_("Checking Package GPG Signatures"))
            progress.tasks.set_extra_label('download', "")
            progress.tasks.next()
        elif state == 'test-transaction':
            progress.set_pulse(True)
            progress.set_header(_("Running RPM Test Transaction"))
            progress.tasks.next('gpg-check')
        elif state == 'transaction':
            progress.set_pulse(False)
            progress.set_header(_("Running RPM Transaction"))
            progress.tasks.next()

    def gpg_check(self, po, userid, hexkeyid):
        """  Confirm GPG key  """
        msg = _('Do you want to import GPG Key : %s \n') % hexkeyid
        msg += "  %s \n" % userid
        msg += _("Needed by %s") % str(po)
        return questionDialog(self.frontend.window, msg)

    def media_change(self, prompt_first, media_id, media_name, media_num):
        '''
        Media change callback, triggered from the yum backend, when a media
        change is needed.
        @param prompt_first: should prompt user before looking for the media
        @param media_id: An ID to make sure we got the required disc
        @param media_name: The media name
        @param media_num: The media discnum
        @return: the mountpoint of the requested media or None to cancel
        '''
        prompt = prompt_first
        if media_num:
            msg = _("Please insert media labeled %s #%d.") % (media_name, media_num)
        else:
            msg = _("Please insert media labeled %s.") % (media_name,)
        while(1): # breaks if the user cancels it or if we found the needed media
            if prompt:
                rc = okCancelDialog(self.frontend.window, msg)
                if not rc: return None
            mp = self._get_mount_point(media_id, media_num)
            if mp: return mp
            prompt = True

    def _get_mount_point(self, media_id, media_num):
        '''
        Get the mount point of a media
        @param media_id: An ID to make sure we got the required disc
        @param media_num: The media discnum
        @return: then mountpoint of the requested media or None if not found
        '''
        try:
            manager = MediaManager()
        except NotImplemented:
            return None
        # check for the needed media in every media provided by yumMediaManager
        for media in manager:
            # mnt now holds the mount point
            mnt = media.acquire()
            # if not mounted skip this media for this loop
            if not mnt:
                continue
            # load ".discinfo" from the media and parse it
            if os.path.exists("%s/.discinfo" % (mnt,)):
                f = open("%s/.discinfo" % (mnt,), "r")
                lines = f.readlines()
                f.close()
                theid = lines[0].strip()
                discs_s = lines[3].strip()
                # if discs_s == ALL then no need to match disc number
                if discs_s != 'ALL':
                    discs = [int(x) for x in discs_s.split(",")]
                    samenum = media_num in discs
                else:
                    samenum = True
                # if the media is different or of different number skip it and loop over
                if media_id == theid and samenum:
                    return mnt
        return None


    def timeout(self, count):
        """
        timeout function call every time an timeout occours
        An timeout occaurs if the server takes more then timeout
        periode to respond to the current action.
        the default timeout is .5 sec.
        """
        self.frontend.timeout(count)

    def exception(self, msg):
        """ debug message """
        self.frontend.exception(unpack(msg))

    def setup(self, offline=False, repos=None):
        ''' Setup the backend'''
        if self.yum_backend_is_running: # Check if backend is already running
            return
        self.frontend.info(_("Starting yum child process"))
        if repos:
            self.frontend.info(_("Using the following repositories :\n%s\n\n") % (','.join(repos)))
        plugins = self.frontend.settings.plugins
        yumdebuglevel = self.frontend.settings.yumdebuglevel
        proxy = self.frontend.settings.proxy.strip()
        yum_conf = self.frontend.settings.yum_conf
        filelog = False
        if 'show_backend' in self.frontend.debug_options:
            filelog = True
        self.debug('Initialize yum backend - BEGIN')
        rc = YumClient.setup(self, debuglevel=yumdebuglevel, plugins=plugins, filelog=filelog, offline=offline, repos=repos, proxy=proxy, yum_conf=yum_conf)
        self.debug('Initialize yum backend - END')
        return rc

    def reset(self):
        ''' Reset the backend, so it can be setup again'''
        self.package_cache.reset()
        rc = YumClient.reset(self)
        if rc:
            self.frontend.info(_("yum backend process is ended"))

    #@TimeFunction
    def get_packages(self, pkg_filter, show_dupes=False):
        '''
        get packages based on filter
        @param pkg_filer: package list filter
        @return: a list of packages
        '''
        if str(pkg_filter) == 'all':
            filters = ['installed', 'available']
        else:
            filters = [pkg_filter]
        rc = []
        # Getting the packages
        for flt in filters:
            if not self.package_cache.is_populated(pkg_filter):
                pkgs = YumClient.get_packages(self, flt, show_dupes)
                self.debug('got %i packages from yum backend' % (len(pkgs)))
                self.package_cache.populate(flt, pkgs)
            else:
               pkgs = self.package_cache._get_packages(pkg_filter)
               self.debug('got %i packages from cache' % (len(pkgs)))
            rc.extend(pkgs)
        self.info(_("%i packages returned") % len(rc))
        return rc

    def get_packages_size(self, ndx):
        '''
        get packages based on size ranges
        @param ndx: size range index
        @return: a list of packages
        '''
        pkgs = YumClient.get_packages_size(self, ndx)
        return self.package_cache.find_packages(pkgs)

    def get_dependencies(self, po):
        reqs = YumClient.get_dependencies(self, po)
        rc = {}
        for req_tup, po in reqs:
            req = prco_tuple_to_string(req_tup)
            cpo = self.package_cache._add(po)
            if req in rc:
                rc[req].append(cpo)
            else:
                rc[req] = [cpo]
        return rc

    def get_packages_repo(self, repoid):
        '''
        get packages based on repoid
        @param repoid: the repo id
        @return: a list of packages
        '''
        pkgs = YumClient.get_packages_repo(self, repoid)
        return self.package_cache.find_packages(pkgs)

    def get_repositories(self):
        '''
        get repositories
        @return: a list of repositories
        '''
        repos = YumClient.get_repos(self)
        return repos


    def enable_repository(self, repoid, enabled=True):
        '''
        set repository enable state
        @param repoid: repo id to change
        @param enabled: repo enable state
        '''
        self.frontend.debug('Setting repository %s (Enabled = %s)' % (repoid, enabled))
        repo = YumClient.enable_repo(self, repoid, enabled)
        return repo

    def get_groups(self):
        '''
        get groups
        @return: a list of groups
        '''
        self.frontend.debug('Getting Group information')
        grps = YumClient.get_groups(self)
        return grps

    def get_group_packages(self, group, grp_filter=None):
        '''
        get packages in a group
        @param group: group id to get packages from
        @param grp_filter: group filters (Enum GROUP)
        '''
        self.frontend.debug('Getting packages in group : %s (FILTER = %s)' % (group, grp_filter))
        pkgs = YumClient.get_group_packages(self, group, grp_filter)
        return self.package_cache.find_packages(pkgs)

    def get_available_by_name(self, name):
        pkgs = YumClient.get_available_by_name(self, name)
        return self.package_cache.find_packages(pkgs)

    def get_available_downgrades(self, po):
        pkgs = YumClient.get_available_downgrades(self, po)
        return self.package_cache.find_packages(pkgs)

    def search(self, keys, sch_filters, show_newest_only, package_type, use_cache=True ):
        '''
        get packages matching keys
        @param keys: list of keys to search for
        @param sch_filters: list of search filter (Enum SEARCH)
        '''
        self.frontend.debug('Seaching for %s in %s (%s)' % (keys, sch_filters, package_type))
        pkgs = YumClient.search(self, keys, sch_filters, show_newest_only, package_type)
        return self.package_cache.find_packages(pkgs)

    def search_prefix(self, prefix, show_newest_only, package_type, use_cache=True):
        '''
        Search for packages with prefix
        @param prefix prefix to search for
        '''
        pkgs = YumClient.search_prefix(self, prefix, show_newest_only, package_type)
        return self.package_cache.find_packages(pkgs)

    def run_command(self, cmd, userlist, use_cache=True):
        '''
        Search for packages with prefix
        @param prefix prefix to search for
        '''
        pkgs = YumClient.run_command(self, cmd, userlist)
        self.frontend.get_progress().hide()
        return self.package_cache.find_packages(pkgs)


class YumexTransactionYum(YumexTransactionBase):
    '''
    Yumex Transaction Base class

    This is a abstract transaction queue for storing unprocessed changes
    to the system and to process the transaction on the system.
    '''

    def __init__(self, backend, frontend):
        '''
        initialize the transaction queue
        @param backend: The current YumexBackend
        @param frontend: the current YumexFrontend
        '''
        YumexTransactionBase.__init__(self, backend, frontend)

    def add(self, po, action):
        '''
        add a package to the queue
        @param po: package to add to the queue
        '''
        self.backend.add_transaction(po.id, action)

    def remove(self, po):
        '''
        remove a package from the queue
        @param po: package to remove from the queue
        '''
        self.backend.remove_transaction(po.id)

    def reset(self):
        '''
        reset the transaction queue
        '''
        self.backend.reset_transaction()


    def has_item(self, po):
        '''
        check if a package is already in the queue
        @param po: package to check for
        '''
        pass

    def add_group(self, grp):
        '''
        Add a group to the queue
        @param grp: group to add to queue
        '''
        pass

    def remove_group(self, grp):
        '''
        Remove a group from the queue
        @param grp: group to add to queue
        '''
        pass

    def has_group(self, grp):
        '''
        Check if a group is in the  queue
        @param grp: group to check for
        '''
        pass

    def process_transaction(self):
        '''
        Process the packages and groups in the queue
        '''
        progress = self.frontend.get_progress()
        progress.set_header(_("Resolving Dependencies"))
        progress.tasks.reset()
        progress.tasks.run_current()
        rc, msgs, trans, size = self.backend.build_transaction()
        if rc == 2:
            self.frontend.debug('Dependency resolving completed without error')
            #progress.hide()
            if self.frontend.confirm_transaction(trans, size[0]): # Let the user confirm the transaction
                progress.show()
                rc = self.backend.run_transaction()
                progress.tasks.complete_current()
                progress.tasks.set_extra_label('run-trans', "")
                return rc
            else: # Aborted by User
                return None
        else:
            progress.hide()
            title = _("Dependency Resolution Failed")
            text = _("Dependency Resolution Failed")
            longtext = _("Dependency Resolution Errors:")
            longtext += '\n\n'
            for msg in msgs:
                longtext += msg
            # Show error dialog
            dialog = ErrorDialog(self.frontend.ui, self.frontend.window, title, text, longtext, modal=True)
            dialog.run()
            dialog.destroy()
            # Write errors to output page
            self.frontend.error(_('Dependency resolving completed with errors'))
            for msg in msgs:
                self.frontend.error("  %s" % msg)
            return False

    def get_transaction_packages(self):
        '''
        Get the current packages in the transaction queue
        '''
        pkgs = self.backend.list_transaction()
        return [YumexPackageYum(p, self.frontend) for p in pkgs]



