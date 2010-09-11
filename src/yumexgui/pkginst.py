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

# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
import logging
from yumexbase.i18n import _, P_
# pylint: enable-msg=W0611

class PkgInstFrontend(YumexFrontendBase):
    '''
    Pkginst Frontend  class

    This is a frontend callback class used by the backend and
    transaction to notify the frontend about changes.
    '''

    def __init__(self, backend, progress):
        ''' Setup the frontend callbacks '''
        self.logger = logging.getLogger(YUMEX_LOG)
        YumexFrontendBase.__init__(self, backend, progress)
        
    def set_state(self, state):
        ''' set the state of work '''
        pass

    def get_progress(self):
        ''' Get the current progress object '''
        return self._progress

    def set_progress(self, progress):
        ''' trigger at progress update'''
        self._progress = progress

    def confirm_transaction(self, transaction, size):
        ''' confirm the current transaction'''
        dialog = self.transactionConfirm
        dialog.populate(transaction,size)
        ok = dialog.run()
        dialog.destroy()
        return ok

    def error(self, msg, exit_pgm=False):
        ''' Write an error message to frontend '''
        self.logger.error('ERROR: %s' % msg)
        if sys.stderr.isatty():
            print >> sys.stderr, 'ERROR: %s' % msg
        self.refresh()
        if exit_pgm:
            sys.exit(1)
            

    def warning(self, msg):
        ''' Write an warning message to frontend '''
        self.logger.warning('WARNING: %s' % msg)
        if sys.stdout.isatty():
            print >> sys.stdout, 'WARNING: %s' % msg
        self.refresh()

    def info(self, msg):
        ''' Write an info message to frontend '''
        if sys.stdout.isatty():
            print >> sys.stdout, msg
        self.logger.info(msg)
        self.refresh()

    def debug(self, msg):
        ''' Write an debug message to frontend '''
        if self.settings.debug:
            print "DEBUG:", msg
            self.logger.debug('DEBUG: %s' % msg)
        self.refresh()

    def exception(self, msg):
        ''' handle an expection '''
        #self.progress.hide()
        print "Exception:", msg
        title = "Exception in Yum Extender"
        text = "An exception was triggered "
        longtext = msg            
        # Show error dialog    
        dialog = ErrorDialog(self.ui, self.window, title, text, longtext, modal=True)
        dialog.run()
        dialog.destroy()
        try: # try to close nicely
            self.main_quit()
        except: # exit
            sys.exit(1)

    def reset(self):
        ''' trigger a frontend reset '''
        pass

    def timeout(self, count):
        '''
        Called on backend timeout (default 0.1 sec)
        @param count: Number of calls, since start of current action
        '''
        if (count > 0 and count % 600 == 0):
            self.debug('Current backend action has been running for %i min' % int(count / 600))
        self.refresh()
        
    def refresh(self):     
        '''
        Refresh the gui and pulse the progress if enabled and in pulse mode
        '''
        progress = self.get_progress()  
        if progress:        
            if progress.is_active() and progress.is_pulse():
                progress.pulse()
        doGtkEvents()
        
class PkgInstHandlers(Controller):
    ''' This class contains all signal callbacks '''
    
    
    def __init__(self):
        '''
        Init the signal callback Controller 
        '''
        # init the Controller Class to connect signals etc.
        Controller.__init__(self, BUILDER_PKGINST , 'pkginst', domain='yumex')
        self.current_repos = []
                
# Signal handlers
      
    def quit(self):
        ''' destroy Handler '''
        # Save the windows size and separator position
        self.backend.debug("Quiting the program !!!")
        progress = self.get_progress()
        progress.set_pulse(True)
        progress.set_title(_("Terminating Yum Backend"))
        progress.set_header(_("Terminating the Yum Backend"))
        progress.show()
        
        try:
            self.backend.reset()
        except:
            pass
        progress.set_pulse(False)
        progress.hide()
        self.backend.debug("Backend reset completted")

    # Menu
        
    def on_fileQuit_activate(self, widget=None, event=None):
        '''
        Menu : File -> Quit
        '''
        self.main_quit()

    def on_helpAbout_activate(self, widget=None, event=None):
        '''
        Menu : Help -> About
        '''
        self.ui.About.run()
        self.ui.About.hide()
        #okDialog(self.window, "This function has not been implemented yet")
        self.debug("Help -> About")

        
    def on_packageSearch_activate(self, widget=None, event=None):
        '''
        Enter pressed in the search field
        '''
        busyCursor(self.window)
        self.packageInfo.clear()
        filters = ['name', 'summary', 'description']
        keys = self.ui.packageSearch.get_text().split(' ')
        pkgs = self.backend.search(keys, filters, use_cache=False)
        self.packages.add_packages(pkgs)
        normalCursor(self.window)

    def on_packageSearch_icon_press(self, widget, icon_pos, event):
        '''
        icon pressed in the search field
        '''
        if 'GTK_ENTRY_ICON_SECONDARY' in str(icon_pos):
            self.ui.packageSearch.set_text('')
            self.packageInfo.clear()
            self.packages.clear()
            self.window.set_focus(self.ui.packageSearch) # Default focus on search entry
            
        else:
            self.on_packageSearch_activate()
        
    def on_packageView_cursor_changed(self, widget):    
        '''
        package selected in the view 
        @param widget: the view widget
        '''
        (model, iterator) = widget.get_selection().get_selected()
        if model != None and iterator != None:
            pkg = model.get_value(iterator, 0)
            if pkg:
                if pkg.action == "u":
                    self.packageInfo.update(pkg, update=True)
                else:
                    self.packageInfo.update(pkg)

    def on_packageClear_clicked(self, widget=None, event=None):
        '''
        The clear search button 
        '''
            

    def on_packageSelectAll_clicked(self, widget=None, event=None):
        '''
        The Packages Select All button
        '''
        self.packages.selectAll()

    def on_packageUndo_clicked(self, widget=None, event=None):
        '''
        The Package Undo Button
        '''
        self.packages.deselectAll()
        
        
    def on_ShowOutput_toggled(self, widget=None, event=None):
        self.debug("View -> Show Output")
        enabled = widget.get_active()
        if enabled:
            self.ui.outputPage.show()
        else:
            self.ui.outputPage.hide()
            

    def on_ShowQueue_toggled(self, widget=None, event=None):
        self.debug("View -> Show Queue")
        enabled = widget.get_active()
        if enabled:
            self.ui.queuePage.show()
        else:
            self.ui.queuePage.hide()
            
            
    def on_Execute_clicked(self, widget=None, event=None):
        '''
        The Queue/Packages Execute button
        '''
        self.debug("Starting pending actions processing")
        self.process_transaction(action="queue")
        self.debug("Ended pending actions processing")

    def on_queueOpen_clicked(self, widget=None, event=None):
        '''
        Queue Open Button
        '''
        self.debug("Queue Open")
    
    def on_queueSave_clicked(self, widget=None, event=None):
        '''
        Queue Save button
        '''
        self.debug("Queue Save")
    
    def on_queueRemove_clicked(self, widget=None, event=None):
        '''
        Queue Remove button
        '''
        self.queue.deleteSelected()

# Progress dialog    
        
    def on_progressCancel_clicked(self, widget=None, event=None):
        '''
        The Progress Dialog Cancel button
        '''
        self.debug("Progress Cancel pressed")
                
        

class PkgInstApplication(PkgInstHandlers, PkgInstFrontend):
    """
    The Yum Extender main application class 
    """
    
    def __init__(self, backend):
        '''
        Init the Yumex Application
        @param backend: The backend instance class
        '''
        self._network = NetworkCheckNetworkManager()
        self.cfg = YumexOptions()
        self.cfg.dump()
        self.progress = None
        self.logger = logging.getLogger(YUMEX_LOG)
        self.debug_options = []        
        #(self.cmd_options, self.cmd_args) = self.cfg.get_cmd_options()
        self.backend = backend(self)
        PkgInstHandlers.__init__(self)
        progress = Progress(self.ui, self.window)
        PkgInstFrontend.__init__(self, self.backend, progress)
        self.debug_options = [] # Debug options set in os.environ['YUMEX_DBG']        
        self.package_cache = PackageCache(self.backend, self)
        self._packages_loaded = False
        self.key_bindings = gtk.AccelGroup()
        self._network = NetworkCheckNetworkManager()
        self.repo_popup = None # Repo page popup menu 
        self.show_dupes = True # show duplicate available packages

    @property
    def is_offline(self):
        if self.settings.disable_netcheck: # we are not offline if diaable-netcheck is enabled
            return False
        rc = self._network.check_network_connection()
        if rc: # do we have a real network state
            if self._network.is_connected == False:
                return True
            else:
                return False
        else: # Network connection can't be checked, so act as online  
            return False
        
    
    @property
    def settings(self):
        '''
        easy access property for current settings
        '''
        return self.cfg.settings

    
    def run(self):
        '''
        Run the application
        '''
        # setup
        try:
            self.setup_gui()
            self.backend.setup()
            gtk.main()
        except YumexBackendFatalError, e:
            self.handle_error(e.err, e.msg)

    def handle_error(self, err, msg):        
        '''
        Error message handler
        @param err: error type
        @param msg: error message
        '''
        quit = True
        title = _("Fatal Error")
        if err == 'lock-error': # Cant get the yum lock
            text = _("Can't start the yum backend")
            longtext = _("Another program is locking yum")
            longtext += '\n\n'            
            longtext += _('Message from yum backend:')            
            longtext += '\n\n'            
            longtext += msg            
        elif err == "repo-error":
            text = _("Error in repository setup")
            longtext = msg
            longtext += '\n\n'
            longtext += _('You can try starting \'yumex -n\' from a command line\n')
            longtext += _('and deseleting the repositories causing problems\n')
            longtext += _('and try again.\n')
            progress = self.get_progress()
            progress.hide()
            #quit = False
        elif err == "backend-error":
            text= _('Fatal Error in backend restart')
            longtext = _("Backend could not be closed")
            longtext += '\n\n'
            longtext += msg
        else:
            text = _("Fatal Error : ") + err
            longtext = msg
        # Show error dialog    
        dialog = ErrorDialog(self.ui, self.window, title, text, longtext, modal=True)
        dialog.run()
        dialog.destroy()
        self.error(text)
        self.error(longtext)
        if quit:
            self.main_quit()
                    
       
            
# shut up pylint whinning about attributes declared outside __init__
# pylint: disable-msg=W0201

    def setup_gui(self):
        '''
        Setup the gui
        '''
        
        #Setup About dialog
        self.ui.About.set_version(const.__yumex_version__)

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
        self.ui.queuePage.resize(self.settings.win_width,self.settings.win_height/2)
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
        progress.show()
        pkgs = self.package_cache.get_packages("none")
        self.debug("Initializing the Yum Backend - END")
        progress.set_pulse(False)
        progress.hide()
        self.window.set_focus(self.ui.packageSearch) # Default focus on search entry
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


    def process_queue(self):
        '''
        Process the pending actions in the queue
        '''
        queue = self.queue.queue
        if queue.total() == 0:
            okDialog(self.window,_("The pending action queue is empty")) 
            return False        
        self.backend.transaction.reset()
        for action in ('install', 'update', 'remove','obsolete'):
            pkgs = queue.get(action[0])
            for po in pkgs:
                self.backend.transaction.add(po, action)
        return True

    def process_transaction(self, action="queue", tid=None):
        '''
        '''
        rc = False
        try:
            self.window.present()  # Make the main window show on top
            progress = self.get_progress()
            progress.set_pulse(True)        
            progress.set_title(_("Processing pending actions"))
            progress.set_header(_("Preparing the transaction"))
            progress.show_tasks()
            progress.show()        
            if action == "queue":
                rc = self.process_queue()
            if not rc: # the transaction population failed
                return

            rc = self.backend.transaction.process_transaction()   
            progress.hide_tasks()
            progress.hide()        
            if rc: # Transaction ok
                self.info(_("Transaction completed successfully"))
                progress.hide()        
                msg = _("Transaction completed successfully")
                msg += _("\n\nDo you want to exit Yumex Package Installer ?")
                rc = questionDialog(self.window, msg) # Ask if the user want to Quit
                if rc:
                    self.main_quit() # Quit Yum Extender
                self.reload()
            elif rc == None: # Aborted by user
                self.warning(_("Transaction Aborted by User"))
            else:
                msg = _("Transaction completed with errors,\n check output page for details")
                okDialog(self.window,msg)
                
            progress.set_pulse(False)        
        except YumexBackendFatalError, e:
            self.handle_error(e.err, e.msg)

