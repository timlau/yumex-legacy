#!/usr/bin/python -tt
# -*- coding: iso-8859-1 -*-
#    Yum Exteder (yumex) - A GUI for yum
#    Copyright (C) 2008-2010 Tim Lauridsen < tim<AT>yum-extender<DOT>org >
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

# yum extender pkginst tool

'''
pkginst main module
'''

import sys
import gtk
import pango
import pwd
#import time

from datetime import date

from yumexgui.gui import Notebook, PackageCache, PackageInfo
from yumexgui.dialogs import Progress, TransactionConfirmation, ErrorDialog, okDialog, \
                             questionDialog, Preferences, okCancelDialog
from yumexbase.network import NetworkCheckNetworkManager                             
from guihelpers import  Controller, TextViewConsole, doGtkEvents, busyCursor, normalCursor, doLoggerSetup
from yumexgui.views import YumexPackageView, YumexQueueView, YumexPackageViewSorted
from yumexbase.constants import *
from yumexbase import YumexFrontendBase, YumexBackendFatalError
import yumexbase.constants as const
from yumexbase.conf import YumexOptions
from yumexgui.pkginst import PkgInstFrontend, PkgInstHandlers, PkgInstApplication

# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
import logging
from yumexbase.i18n import _, P_
# pylint: enable-msg=W0611

class PkgUpdaterApplication(PkgInstApplication):
    """
    The Yum Extender main application class 
    """
    
    def __init__(self, backend):
        '''
        Init the Yumex Application
        @param backend: The backend instance class
        '''
        PkgInstApplication.__init__(self, backend)
            
# shut up pylint whinning about attributes declared outside __init__
# pylint: disable-msg=W0201

    def setup_gui(self):
        '''
        Setup the gui
        '''
        
        #Setup About dialog
        self.ui.About.set_version(const.__yumex_version__)
        self.window.set_title("Yumex Updater")

        # Calc font constants based on default font 
        DEFAULT_FONT = self.window.get_pango_context().get_font_description()
        const.XSMALL_FONT.set_size(DEFAULT_FONT.get_size() - 2 * 1024)
        const.SMALL_FONT.set_size(DEFAULT_FONT.get_size() - 1 * 1024)
        const.BIG_FONT.set_size(DEFAULT_FONT.get_size() + 4 * 1024)
        font_size = const.SMALL_FONT.get_size() / 1024
        # Setup Output console
        self.output = TextViewConsole(self.ui.outputText, font_size=font_size)
        self.queue = YumexQueueView(self.ui.queueView)

        if self.settings.use_sortable_view:
            self.packages = YumexPackageViewSorted(self.ui.packageView, self.queue)
        else:
            self.packages = YumexPackageView(self.ui.packageView, self.queue)
            
        self.packageInfo = PackageInfo(self.window, self.ui.packageInfo,
                                       self.ui.packageInfoSelector, self, font_size=font_size)
        # setup transaction confirmation dialog
        self.transactionConfirm = TransactionConfirmation(self.ui, self.window)
        # setup yumex log handler
        self.log_handler = doLoggerSetup(self.output, YUMEX_LOG, logfmt='%(asctime)s : %(message)s')
        # Set saved windows size and separator position
        if self.settings.win_height > 0 and self.settings.win_width > 0:
            self.window.resize(self.settings.win_width,self.settings.win_height)
            if self.settings.win_sep > 0:
                self.ui.packageSep.set_position(self.settings.win_sep)
        self.ui.outputPage.resize(self.settings.win_width,self.settings.win_height/2)
        self.ui.outputPage.set_title("Output - Yumex Updater")
        self.ui.queuePage.resize(self.settings.win_width,self.settings.win_height/2)
        self.ui.queuePage.set_title("Action Queue - Yumex Updater")
        self.ui.packageSearch.hide()
        self.ui.packageSelectAll.show()
        self.window.show()

        # check network state
        if self.is_offline:
            self.info(_("Not connected to an network"))
            rc = questionDialog(self.window,_("Not connected to an network.\nDo you want to continue "))
            if not rc:
                self.main_quit()
        else:
            if self.settings.disable_netcheck:
                self.info(_("network connection state check is disabled"))
            elif self._network.is_connected == None:
                self.info(_("Can't detect the network connection state"))
            else:
                self.info(_("Connected to an network"))
        self.init_yum_backend(show_dupes=self.show_dupes) # repopulate the package cache

# pylint: enable-msg=W0201

    def init_yum_backend(self, repos=None, show_dupes=False):
        '''
        Initialize the yum backen
        @param repos: a list of enabled repositories to use, None = use the current ones
        '''
        if not repos:
            repos = self.current_repos
        progress = self.get_progress()
        progress.set_pulse(True)
        self.debug("Initializing the Yum Backend - BEGIN")
        self.backend.setup(self.is_offline, repos)
        progress.set_title(_("Initializing the Yum Backend"))
        progress.set_header(_("Initializing the Yum Backend"))
        progress.set_header(_("Getting Updated Packages"))
        progress.show()
        pkgs = self.package_cache.get_packages(FILTER.updates)
        obs = self.package_cache.get_packages(FILTER.obsoletes)
        pkgs.extend(obs)
        label = "updates & obsoletes"
        self.debug('START: Adding %s packages to view' % label)
        self.packages.add_packages(pkgs, progress=self.progress)        
        self.debug("Initializing the Yum Backend - END")
        progress.set_pulse(False)
        progress.hide()
        self._packages_loaded = True

    def reload(self, repos=None):
        '''
        Reset current data and restart the backend 
        @param repos: a list of enabled repositories to use, None = use the current ones
        '''
        try:
            if not repos:
                repos = self.current_repos
            self.backend.reset()                    # close the backend
            self.package_cache.reset()              # clear the package cache
            self.queue.queue.clear()                # clear the pending action queue
            self.queue.refresh()                    # clear the pending action queue
            self.ui.packageSearch.set_text('')
            self.packageInfo.clear()
            self.packages.clear()            
            self.init_yum_backend(show_dupes=self.show_dupes) # repopulate the package cache
            return True
        except YumexBackendFatalError, e:
            progress = self.get_progress()
            progress.hide()
            self.handle_error(e.err, e.msg)
            return False


