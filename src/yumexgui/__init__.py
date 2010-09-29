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

# yum extender gui module

'''
Yum Extender GUI main module
'''

import sys
import gtk
import pango
import pwd
import time

from datetime import date

from yumexgui.gui import Notebook, PackageInfo
from yumexgui.dialogs import Progress, TransactionConfirmation, ErrorDialog, okDialog, \
                             questionDialog, Preferences, okCancelDialog, SearchOptions, \
                             TestWindow
from yumexbase.network import NetworkCheckNetworkManager                             
from guihelpers import  Controller, TextViewConsole, doGtkEvents, busyCursor, normalCursor, doLoggerSetup
from yumexgui.views import YumexPackageView, YumexQueueView, YumexRepoView, YumexGroupView,\
                           YumexCategoryContentView, YumexCategoryTypesView, YumexHistoryView, \
                           YumexPackageViewSorted, YumexHistoryPackageView
from yumexbase.constants import *
from yumexbase import YumexFrontendBase, YumexBackendFatalError
import yumexbase.constants as const
from yumexbase.conf import YumexOptions

# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
import logging
from yumexbase.i18n import _, P_
# pylint: enable-msg=W0611

class YumexFrontend(YumexFrontendBase):
    '''
    Yumex Frontend  class

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
        self.refresh()
        if exit_pgm:
            sys.exit(1)
            

    def warning(self, msg):
        ''' Write an warning message to frontend '''
        self.logger.warning('WARNING: %s' % msg)
        self.refresh()

    def info(self, msg):
        ''' Write an info message to frontend '''
        self.logger.info(msg)
        self.refresh()

    def debug(self, msg, name=None):
        ''' Write an debug message to frontend '''
        if not name:
            classname = __name__.split('.')[-1]
            name = classname + "."+sys._getframe(1).f_code.co_name                
        if self.settings.debug:
            if name:
                self.logger.debug(msg+"   <%s>" % name)
            else:
                self.logger.debug(msg)
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
        
class YumexHandlers(Controller):
    ''' This class contains all signal callbacks '''
    
    
    def __init__(self):
        '''
        Init the signal callback Controller 
        '''
        # init the Controller Class to connect signals etc.
        Controller.__init__(self, BUILDER_FILE , 'main', domain='yumex')
        self._last_filter = None
        self.default_repos = []
        self.current_repos = []
        self._resized = False
        self._current_active = None
        self.current_category = None
        self.last_queue_text = ""
        
                
# Signal handlers
      
    def quit(self):
        ''' destroy Handler '''
        # Save the windows size and separator position
        try:
            width, height = self.window.get_size()
            if self._resized:
                width = width - 150
            setattr( self.cfg.conf_settings, 'win_width',width)
            setattr( self.cfg.conf_settings, 'win_height',height)
            pos = self.ui.packageSep.get_position()
            setattr( self.cfg.conf_settings, 'win_sep',pos)
            self.cfg.save()
            
        except:
            self.backend.info("Error in saving window size")
        self.backend.debug("Quiting the program !!!")
        try:
            self.backend.reset() # Close the yum backend
            self.backend._close() # Close the backend launcher
        except:
            pass
        self.backend.debug("Backend reset completted")

    # Menu
        
    def on_fileQuit_activate(self, widget=None, event=None):
        '''
        Menu : File -> Quit
        '''
        self.main_quit()

    def on_editPref_activate(self, widget=None, event=None):
        '''
        Menu : Edit -> Preferences
        '''
        #okDialog(self.window, "This function has not been implemented yet")
        self.debug("Edit -> Preferences")
        self.preferences.run()
        self.preferences.destroy()

    def on_proNew_activate(self, widget=None, event=None):
        '''
        Menu : Profile -> New
        '''
        okDialog(self.window, "This function has not been implemented yet")
        self.debug("Profiles -> New")

    def on_proSave_activate(self, widget=None, event=None):
        '''
        Menu : Profile -> Save
        '''
        okDialog(self.window, "This function has not been implemented yet")
        self.debug("Profiles -> Save")
        
    def on_helpAbout_activate(self, widget=None, event=None):
        '''
        Menu : Help -> About
        '''
        self.ui.About.run()
        self.ui.About.hide()
        #okDialog(self.window, "This function has not been implemented yet")
        self.debug("Help -> About")
        
        
# Options

    def on_option_nogpgcheck_toggled(self, widget=None, event=None):
        self.backend.set_option('gpgcheck',not widget.get_active(),on_repos=True)
        
    def on_option_skipbroken_toggled(self, widget=None, event=None):
        self.backend.set_option('skip_broken', widget.get_active())


    def on_viewPackages_activate(self, widget=None, event=None):
        '''
        Menu : View -> Packages
        '''
        self.notebook.set_active("package")

    def on_viewQueue_activate(self, widget=None, event=None):
        '''
        Menu : View -> Queue
        '''
        self.notebook.set_active("queue")

    def on_viewRepo_activate(self, widget=None, event=None):
        '''
        Menu : View -> Repo
        '''
        self.notebook.set_active("repo")
        
    def on_viewOutput_activate(self, widget=None, event=None):
        '''
        Menu : View -> Output
        '''
        self.notebook.set_active("output")
        
    def on_viewHistory_activate(self, widget=None, event=None):
        '''
        Menu : View -> History
        '''
        self.notebook.set_active("history")
    # Package Page    
    
    def on_searchTypeAhead_toggled(self, widget=None, event=None):
        active = self.ui.searchTypeAhead.get_active()
        self.typeahead_active = active
        self.window.set_focus(self.ui.packageSearch) # Default focus on search entry

    
    def on_searchOptions_clicked(self, widget=None, event=None):
        self.search_options.run()
        self.window.set_focus(self.ui.packageSearch) # Default focus on search entry
        
    def on_packageSearch_changed(self, widget=None, event=None):
        keys = self.ui.packageSearch.get_text().split(' ')
        if not self.typeahead_active or len(keys) > 1:
            return
        txt = keys[0]
        if len(txt) >= 3:
            self.ui.packageSearch.set_sensitive(False)
            busyCursor(self.window)
            self.debug("SEARCH : %s" % txt)
            pkgs = self.backend.search_prefix(txt)
            self.debug("SEARCH : got %i packages" % len(pkgs))
            if not self.settings.search:
                self.ui.packageFilterBox.hide()
                if self._last_filter:
                    self._last_filter.set_active(True)            
            self.packages.add_packages(pkgs)
            progress = self.get_progress()
            progress.hide()
            self.ui.packageSearch.set_sensitive(True)
            normalCursor(self.window)
            self.window.set_focus(self.ui.packageSearch) # Default focus on search entry
            
        
    def on_packageSearch_activate(self, widget=None, event=None):
        '''
        Enter pressed in the search field
        '''
        if self._packages_loaded:
            busyCursor(self.window)
            self.packageInfo.clear()
            filters = self.search_options.get_filters()
            keys = self.ui.packageSearch.get_text().split(' ')
            pkgs = self.backend.search(keys, filters)
            if not self.settings.search:
                self.ui.packageFilterBox.hide()
                if self._last_filter:
                    self._last_filter.set_active(True)            
            self.packages.add_packages(pkgs)
            progress = self.get_progress()
            progress.hide()
            normalCursor(self.window)

    def on_packageSearch_icon_press(self, widget, icon_pos, event):
        '''
        icon pressed in the search field
        '''
        if 'GTK_ENTRY_ICON_SECONDARY' in str(icon_pos):
            self.ui.packageSearch.set_text('')
            if not self.settings.search:
                self.ui.packageFilterBox.show()
                if self._last_filter:
                    self._last_filter.clicked()
            
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
                print "Starting pkgInfo :", str(pkg)
                start = time.time()                
                self.packageInfo.update(pkg)
                end = time.time()
                print "Ending pkgInfo : %.2f " % (end-start)

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
        self.queue.queue.remove_all_groups()
        self.groups.reset_queued()
        
        
    def on_packageFilter_changed(self, widget, active):
        '''
        Package filter radiobuttons
        @param widget: The radiobutton there is changed
        @param active: the button number 0 = Updates, 1 = Available, 2 = Installed, 3 = Groups, 4 = Category
        '''
        if widget.get_active():
            busyCursor(self.window, True)
            self._last_filter = widget
            self._current_active = active
            self.packageInfo.clear()
            self.packages.clear()
            self.ui.packageSearch.set_text('')        
            self.ui.groupVBox.hide()
            self.ui.categoryWindow.hide()
            self.ui.leftBox.hide()
            if active in ['updates', 'available', 'installed', 'all']: # Updates,Available,Installed
                if active == 'updates': # Show only SelectAll when viewing updates
                    self.ui.packageSelectAll.show()
                else:
                    self.ui.packageSelectAll.hide()
                if self._resized:
                    width, height = self.window.get_size()
                    self.window.resize(width - 150, height)
                    self._resized = False
                self.window.set_focus(self.ui.packageSearch) # Default focus on search entry
                self.debug('START: Getting %s packages' % active)
                self.backend.setup()
                label = active
                progress = self.get_progress()
                progress.set_pulse(True)
                filter = active
                progress.set_title(PACKAGE_LOAD_MSG[filter])
                progress.set_header(PACKAGE_LOAD_MSG[filter])
                progress.show()
                pkgs = self.backend.get_packages(getattr(FILTER,active))
                # if Updates, then add obsoletes too
                if active == 'updates':
                    obs = self.backend.get_packages(getattr(FILTER,'obsoletes'))
                    pkgs.extend(obs)
                    label = "updates & obsoletes"
                progress.set_header(_('Adding Packages to view'))
                self.info(_('Adding Packages to view'))
                self.debug('START: Adding %s packages to view' % label)
                self.packages.add_packages(pkgs, progress=progress)                    
                self.info(_('Added %i Packages to view') % len(pkgs))
                progress.set_pulse(False)
                progress.hide()
                self.debug('END: Getting %s packages' % active)
            else:
                if not self._resized:
                    width, height = self.window.get_size()
                    self.window.resize(width + 150, height)
                    self._resized = True
                self.ui.leftBox.show()
                self.packages.clear()
                if active == 'groups': # Groups
                    self.setup_groups()
                    self.ui.groupVBox.show_all()
                elif active == 'categories': # Categories
                    self.ui.categoryWindow.show_all()
            normalCursor(self.window)

    def on_categoryContent_cursor_changed(self, widget):
        '''
        Category Content element selected
        '''
        (model, iterator) = widget.get_selection().get_selected()
        if model != None and iterator != None:
            id = model.get_value(iterator, 0)
            self.packages.clear()
            if self.current_category == 'size':
                pkgs = self.backend.get_packages_size(id)
                self.packages.add_packages(pkgs)
            elif self.current_category == 'repo':
                pkgs = self.backend.get_packages_repo(id)
                self.packages.add_packages(pkgs)
                
            
    def on_categoryTypes_cursor_changed(self, widget):
        '''
        Category Type element selected
        '''
        (model, iterator) = widget.get_selection().get_selected()
        if model != None and iterator != None:
            id = model.get_value(iterator, 0)
            self.current_category = id
            self.packages.clear()
            if id == 'repo':
                data = [(repo,repo) for repo in sorted(self.current_repos)]
                self.category_content.populate(data)
            #elif id == 'age':
            #    self.category_content.populate(const.CATEGORY_AGE)
            elif id == 'size':
                self.category_content.populate(const.CATEGORY_SIZE)
        
    def on_groupView_cursor_changed(self, widget):
        '''
        Group/Category selected in groupView
        @param widget: the group view widget
        '''
        (model, iterator) = widget.get_selection().get_selected()
        if model != None and iterator != None:
            desc = model.get_value(iterator, 5)
            self.groupInfo.clear()
            self.groupInfo.write(desc)
            self.groupInfo.goTop()
            isCategory = model.get_value(iterator, 4)
            if not isCategory:
                grpid = model.get_value(iterator, 2)
                pkgs = self.backend.get_group_packages(grpid, grp_filter=GROUP.all)
                self.packages.add_packages(pkgs)
            
    # Repo Page    
        
    def on_repoRefresh_clicked(self, widget=None, event=None):
        '''
        Repo refresh button
        '''
        repos = self.repos.get_selected()
        self.current_repos = repos
        rc = self.reload(repos)
        return rc
        
    def on_repoUndo_clicked(self, widget=None, event=None):
        '''
        Repo undo button
        '''
        self.repos.populate(self.default_repos)
        
    def on_repoView_button_press_event(self, treeview, event):
        if event.button == 3: # Right Click
            x = int(event.x)
            y = int(event.y)
            t = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor( path, col, 0)
                store = treeview.get_model() 
                iter = store.get_iter( path )
                state = store.get_value(iter,0)
                popup = self.get_repo_popup(state,path)
                popup.popup( None, None, None, event.button, t)
            return True


    def on_repo_popup_other(self,widget,action_id,path):
        if action_id.startswith('clean-'):
            what = action_id.split("-")[1]
            rc = okCancelDialog(self.window,_("Do you want to clean %s from the yum cache") % what)
            if rc:
                self.backend.clean(what)
                
        
    def on_repo_popup_enabled(self,widget,enable,path):
        '''
        
        @param widget:
        @param enable: repo persistent enable state (True = enable, False = disable)
        @param path: treeview path for current item
        '''
        store = self.ui.repoView.get_model()
        iter = store.get_iter( path )
        id = store.get_value(iter,1)
        store.set_value(iter,0,enable)
        self.backend.enable_repo_persistent( id, enable)
        
    # Queue Page    
    
    def on_QueueEntry_icon_press(self, widget, icon_pos, event):
        '''
        icon pressed in the search field
        '''
        if 'GTK_ENTRY_ICON_SECONDARY' in str(icon_pos):
            pass

    def on_QueueEntry_changed(self, widget=None, event=None):
        txt = self.ui.QueueEntry.get_text()
        self.ui.QueueEntry.set_position(-1)
        print "QUEUE_ENTRY",txt, self.ui.QueueEntry.get_position()
        if len(txt) == 2 and len(txt) > len(self.last_queue_text):
            if txt in QUEUE_COMMANDS:
                cmd = QUEUE_COMMANDS[txt]+" "
                self.last_queue_text = cmd
                self.ui.QueueEntry.set_text(cmd)
        self.last_queue_text = txt
   
    def on_QueueEntry_activate(self, widget=None, event=None):
        txt = self.ui.QueueEntry.get_text()
        if txt:
            words = txt.split()
            if len(words) > 1:
                cmd = words[0]
                userlist = words[1:]
                print cmd,userlist
                pkgs = self.backend.run_command(cmd,userlist)
                print [str(p)+":"+p.action for p in pkgs]
                for pkg in pkgs:
                    self.queue.queue.add(pkg)
                    pkg.queued = pkg.action      
                    
                self.queue.refresh()
        self.ui.QueueEntry.set_text("")    
        self.last_queue_text = ""

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
        
    def on_Execute_clicked(self, widget=None, event=None):
        '''
        The Queue/Packages Execute button
        '''
        self.debug("Starting pending actions processing")
        self.process_transaction(action="queue")
        self.debug("Ended pending actions processing")
        
        
# History Page

    def on_historySearch_icon_press(self, widget, icon_pos, event):
        '''
        icon pressed in the search field
        '''
        if 'GTK_ENTRY_ICON_SECONDARY' in str(icon_pos):
            self.ui.historySearch.set_text('')
            self.setup_history(force=True)

        
    def on_historySearch_activate(self, widget=None, event=None):
        txt = self.ui.historySearch.get_text()
        pat = txt.split(' ')
        if not pat:
            self.setup_history(force=True)
        else:
            self.search_history(pat)
        
    def on_historyUndo_clicked(self, widget=None, event=None):
        (model, iterator) = self.ui.historyView.get_selection().get_selected()
        if model != None and iterator != None:
            tid = model.get_value(iterator, 0)
            self.debug("Starting history undo")
            self.process_transaction(action="history-undo",tid=tid)
            self.debug("Ended History undo")
    
    def on_historyRedo_clicked(self, widget=None, event=None):
        (model, iterator) = self.ui.historyView.get_selection().get_selected()
        if model != None and iterator != None:
            tid = model.get_value(iterator, 0)
            self.debug("Starting history redo")
            self.process_transaction(action="history-redo",tid=tid)
            self.debug("Ended History redo")
    
    def on_historyRefresh_clicked(self, widget=None, event=None):
        busyCursor(self.window)
        self.setup_history(limit=False,force=True)
        normalCursor(self.window)
    
    
    def on_historyView_cursor_changed(self, widget):
        '''
        a new History element is selected in history view
        '''
        (model, iterator) = widget.get_selection().get_selected()
        if model != None and iterator != None:
            tid = model.get_value(iterator, 0)
            self.show_history_packages(tid)
    
# Progress dialog    
        
    def on_progressCancel_clicked(self, widget=None, event=None):
        '''
        The Progress Dialog Cancel button
        '''
        self.debug("Progress Cancel pressed")
                

class YumexApplication(YumexHandlers, YumexFrontend):
    """
    The Yum Extender main application class 
    """
    
    def __init__(self, backend):
        '''
        Init the Yumex Application
        @param backend: The backend instance class
        '''
        self.logger = logging.getLogger(YUMEX_LOG)
        if sys.stderr.isatty():
            self.doTextLoggerSetup( YUMEX_LOG, logfmt='%(asctime)s : %(levelname)s - %(message)s')
        self._network = NetworkCheckNetworkManager()
        self.cfg = YumexOptions()
        if self.settings.debug:
            self.logger.setLevel(logging.DEBUG)
        self.cfg.dump()
        self.progress = None
        self.debug_options = []        
        #(self.cmd_options, self.cmd_args) = self.cfg.get_cmd_options()
        self.backend = backend(self)
        YumexHandlers.__init__(self)
        progress = Progress(self.ui, self.window)
        YumexFrontend.__init__(self, self.backend, progress)
        self.debug_options = [] # Debug options set in os.environ['YUMEX_DBG']        
        self._packages_loaded = False
        self.key_bindings = gtk.AccelGroup()
        self._network = NetworkCheckNetworkManager()
        self.repo_popup = None # Repo page popup menu 
        self.show_dupes = True # show duplicate available packages
        self.groups_is_loaded = False
        self.history_is_loaded = False
        self.default_search_keys = ['name', 'summary', 'description']
        self.search_keys = ['name', 'summary', 'description', "arch"]
        self.typeahead_active = False

        

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
                    
    def _add_key_to_menu(self, widget, key, mask=gtk.gdk.CONTROL_MASK):
        widget.add_accelerator("activate", self.key_bindings,
                               ord(key), gtk.gdk.CONTROL_MASK, 0)

    def add_keybindings(self):
        self.window.add_accel_group(self.key_bindings)
        self._add_key_to_menu(self.ui.viewPackages,'1')
        self._add_key_to_menu(self.ui.viewQueue,'2')
        self._add_key_to_menu(self.ui.viewRepo,'3')
        self._add_key_to_menu(self.ui.viewOutput,'4')
        
    def fix_gtkbuilder_translations(self):
        '''
        fix stuff, that don't get translated in the gtk.builder xml file
        '''
        # Fix main menues
        menus = ['fileMenu','editMenu','viewMenu','optionsMenu','helpMenu','viewPackages','viewQueue',\
                 'viewRepo','viewOutput','option_skipbroken','option_nogpgcheck','packageRadioUpdates',\
                'packageRadioAvailable','packageRadioInstalled','packageRadioGroups','packageRadioCategories',\
                'packageRadioAll','viewHistory']
        for menu in menus:
            obj = getattr(self.ui,menu)
            label = obj.get_child()
            label.set_label(_(label.get_label()))
            
        tabs = ['prefBasic', 'prefAdvanced']
        for tab in tabs:
            obj = getattr(self.ui,tab)
            obj.set_label(_(obj.get_label()))
            
        # tool tip to fix             
        toolstip_widgets = ['packageRadioUpdates', 'packageRadioAvailable', 'packageRadioInstalled', \
                            'packageRadioGroups','packageRadioCategories', 'packageRadioAll',\
                            'packageSelectAll', 'packageUndo', 'packageExecute',\
                            'searchTypeAhead', 'searchOptions', 'packageSearch', \
                            'queueExecute', 'queueRemove', 'repoRefresh', 'repoUndo', \
                            'historyRefresh', 'historyUndo', 'historyRedo', 'historySearch']
        for widget in toolstip_widgets:
            obj = getattr(self.ui,widget)
            obj.set_tooltip_text(_(obj.get_tooltip_text()))

            
        
        
            
# shut up pylint whinning about attributes declared outside __init__
# pylint: disable-msg=W0201

    def _add_key_binding(self,widget,event,accel):
        keyval,mask = gtk.accelerator_parse(accel)
        widget.add_accelerator(event, self.key_bindings, keyval, mask, 0)
        

    def setup_gui(self):
        '''
        Setup the gui
        '''
        # Fix the translations in gtk.Builder object
        self.fix_gtkbuilder_translations()
        # setup
        self.window.set_title(self.settings.branding_title)
        self.window.add_accel_group(self.key_bindings)
        
        
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
        # Setup main page notebook
        self.notebook = Notebook(self.ui.mainNotebook, self.ui.MainLeftContent, self.key_bindings)
        if self.settings.update_only:
            pkg_title = _("Available Updates")
        elif self.settings.search:
            pkg_title = _("Search for packages")
        else:
            pkg_title = _("Packages")            
        self.notebook.add_page("package", pkg_title , self.ui.packageMain, 
                                icon=ICON_PACKAGES, tooltip=_("Perform actions on packages"),
                                accel = '<Ctrl>1')
        self.notebook.add_page("queue", _("Pending Actions"), self.ui.queueMain, 
                               icon=ICON_QUEUE, tooltip=_("Work with pending actions"),
                                accel = '<Ctrl>2')
        if not self.settings.disable_repo_page:
            self.notebook.add_page("repo", _("Repositories"), self.ui.repoMain, 
                                   icon=ICON_REPOS, tooltip=_("Select active repositories"),
                                accel = '<Ctrl>3')
        if not self.settings.search and not self.settings.update_only:
            self.notebook.add_page("history", _("History"), self.ui.historyMain, 
                               icon=ICON_HISTORY, tooltip=_("Watch yum history"),
                                accel = '<Ctrl>4', callback=self.setup_history)
            self.history_pkg_view = YumexHistoryPackageView(self.ui.historyPkgView, \
                                            self.settings.color_install, \
                                            self.settings.color_normal )

        self.notebook.add_page("output", _("Output"), self.ui.outputMain, 
                               icon=ICON_OUTPUT, tooltip=_("Watch output details"),
                                accel = '<Ctrl>5')
        self.ui.groupView.hide()
        self.notebook.set_active("output")
        # Preferences
        self.preferences = Preferences(self.ui,self.window,self.cfg)
        # setup queue view
        self.queue = YumexQueueView(self.ui.queueView)
        # seach options
        self.search_options = SearchOptions(self.ui, self.window, self.search_keys, self.default_search_keys)
        self.typeahead_active = self.settings.typeahead_search
        active = self.ui.searchTypeAhead.set_active(self.typeahead_active)

        # setup package and package info view
        if self.settings.use_sortable_view:
            self.packages = YumexPackageViewSorted(self.ui.packageView, self.queue)
        else:
            self.packages = YumexPackageView(self.ui.packageView, self.queue, self)
            
        self.packageInfo = PackageInfo(self.window, self.ui.packageInfo,
                                       self.ui.packageInfoSelector, self, font_size=font_size)
        # setup group and group description views
        self.groups = YumexGroupView(self.ui.groupView, self.queue, self)
        self.groupInfo = TextViewConsole(self.ui.groupDesc, font_size=font_size)
        # setup history page
        self.history = YumexHistoryView(self.ui.historyView)
        
        # setup category views
        self.category_types = YumexCategoryTypesView(self.ui.categoryTypes)
        self.category_content = YumexCategoryContentView(self.ui.categoryContent)
        self.setup_categories()
        # setup repo view
        self.repos = YumexRepoView(self.ui.repoView)
        # setup transaction confirmation dialog
        self.transactionConfirm = TransactionConfirmation(self.ui, self.window)
        # setup yumex log handler
        self.log_handler = doLoggerSetup(self.output, YUMEX_LOG, logfmt='%(asctime)s : %(message)s')
        # Set saved windows size and separator position
        if self.settings.win_height > 0 and self.settings.win_width > 0:
            self.window.resize(self.settings.win_width,self.settings.win_height)
            if self.settings.win_sep > 0:
                self.ui.packageSep.set_position(self.settings.win_sep)
        self.window.show()
        # set up the package filters ( updates, available, installed, groups)
        self.setup_filters()
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

        # load packages and groups 
        # We cant disable both repo page and auto refresh
        if self.settings.autorefresh or self.settings.disable_repo_page: 
            self.populate_package_cache()
            self.notebook.set_active("package")
        else:
            self.backend.setup(repos=self.current_repos)
            self.notebook.set_active("repo")
        # setup repository view    
        repos = self.backend.get_repositories()
        self.repos.populate(repos)
        self.default_repos = repos
        active_repos = self.repos.get_selected()
        self.current_repos = active_repos
        self._add_key_binding(self.ui.packageSearch, 'activate', '<alt>s')
        if self.settings.search:            # Search only mode
            self.ui.packageFilterBox.hide()
            self.window.set_focus(self.ui.packageSearch) # Default focus on search entry
        elif self.settings.update_only:     # Update only mode
            self.ui.packageFilterBox.hide()
            self.ui.packageSearchBox.hide()
            self.ui.packageRadioUpdates.clicked()
        else:
            # setup default package filter (updates)
            self.ui.packageRadioUpdates.clicked()
            self.window.set_focus(self.ui.packageSearch) # Default focus on search entry
        #self.testing()

# pylint: enable-msg=W0201


    def testing(self):
        """
        Test func for lauching a TestWindow for testing new views 
        """
        tw = TestWindow(self.ui,self.backend, self)

    def doTextLoggerSetup( self, logroot, logfmt = '%(message)s', loglvl = logging.INFO):
        ''' Setup Python logging using a TextViewLogHandler '''
        logger = logging.getLogger(logroot)
        logger.setLevel(loglvl)
        formatter = logging.Formatter(logfmt, "%H:%M:%S")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        # shut up pylint whinning about attributes declared outside __init__ (false positive)
        # pylint: disable-msg=W0201
        handler.propagate = False
        # pylint: enable-msg=W0201    
        logger.addHandler(handler)
        return handler


    def _add_menu(self,menu,label,action_id,path):
        mi = gtk.MenuItem (label)
        mi.connect('activate', self.on_repo_popup_other, action_id, path)
        menu.add(mi)
        

    def get_repo_popup(self,enabled,path):
        repo_popup = gtk.Menu()
        if not enabled:
            mi = gtk.MenuItem (_("Enable Permanently"))
            mi.connect('activate', self.on_repo_popup_enabled, True, path)
            repo_popup.add(mi)
        else: 
            mi = gtk.MenuItem (_("Disable Permanently"))
            mi.connect('activate', self.on_repo_popup_enabled, False, path)
            repo_popup.add(mi)
        self._add_menu(repo_popup, _("Clean Metadata"), "clean-metadata", path)
        self._add_menu(repo_popup, _("Clean Packages"), "clean-packages", path)
        self._add_menu(repo_popup, _("Clean DbCache"), "clean-dbcache", path)
        self._add_menu(repo_popup, _("Clean All"), "clean-all", path)
        repo_popup.show_all()
        return repo_popup


    def setup_categories(self):
        cats = [('repo',_('By Repositories')),
                ('size',_('By Size'))
                #('age' ,_('By Age') ))
                ]
                        
        self.category_types.populate(cats)

    def setup_filters(self, filters=None):
        ''' 
        Populate Package Filter radiobuttons
        '''
        if not filters:
            filters = ('Updates', 'Available', 'Installed', 'Groups','Categories','All')
        for attr in filters:
            rb = getattr(self.ui, 'packageRadio' + attr)
            rb.connect('clicked', self.on_packageFilter_changed, attr.lower()) 
            rb.child.modify_font(SMALL_FONT)
            
    def setup_groups(self,force=False):
        '''
        Get Group information and populate the group view
        '''
        if not self.groups_is_loaded or force:
            progress = self.get_progress()
            self.debug("Getting Group information - BEGIN")
            progress.set_title(_("Getting Group information"))
            progress.set_header(_("Getting Group information"))
            progress.set_pulse(True)
            progress.show()
            groups = self.backend.get_groups()
            self.groups.populate(groups)
            progress.hide()
            progress.set_pulse(False)
            self.debug("Getting Group information - END")
            self.groups_is_loaded = True
        
    def populate_package_cache(self, repos=None, show_dupes=False):
        '''
        Get the packagelists and put them in the package cache.
        @param repos: a list of enabled repositories to use, None = use the current ones
        '''
        if not repos:
            repos = self.current_repos
        progress = self.get_progress()
        progress.set_pulse(True)
        self.debug("Getting package lists - BEGIN")
        self.backend.setup(self.is_offline, repos)
        self.debug("Getting package lists - END")
        progress.set_pulse(False)
        progress.hide()
        self._packages_loaded = True

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
            self.notebook.set_active("output")
            progress = self.get_progress()
            progress.set_pulse(True)        
            progress.set_title(_("Processing pending actions"))
            progress.set_header(_("Preparing the transaction"))
            progress.show_tasks()
            progress.show()        
            if action == "queue":
                rc = self.process_queue()
            elif action == "history-undo":
                rc = self.backend.history_undo(tid)
            elif action == "history-redo":
                rc = self.backend.history_redo(tid)
            if not rc: # the transaction population failed
                return

            rc = self.backend.transaction.process_transaction()   
            progress.hide_tasks()
            progress.hide()        
            if rc: # Transaction ok
                self.info(_("Transaction completed successfully"))
                progress.hide()        
                msg = _("Transaction completed successfully")
                msg += _("\n\nDo you want to exit Yum Extender ?")
                rc = questionDialog(self.window, msg) # Ask if the user want to Quit
                if rc:
                    self.main_quit() # Quit Yum Extender
                self.reload()
            elif rc == None: # Aborted by user
                self.warning(_("Transaction Aborted by User"))
                self.notebook.set_active("package")     # show the package page
            else:
                msg = _("Transaction completed with errors,\n check output page for details")
                okDialog(self.window,msg)
                
            progress.set_pulse(False)        
        except YumexBackendFatalError, e:
            self.handle_error(e.err, e.msg)

    def _get_options(self):
        '''
        Store the session based options in the Options menu
        '''
        options = []
        options.append( (self.ui.option_nogpgcheck,self.ui.option_nogpgcheck.get_active()) )
        return options
    
    def _set_options(self,options):
        '''
        Reset the session based options in the Options menu
        '''
        for (option,state) in options:
            option.set_active(state)

    def reload(self, repos=None):
        '''
        Reset current data and restart the backend 
        @param repos: a list of enabled repositories to use, None = use the current ones
        '''
        try:
            self.notebook.set_active("output")
            if not repos:
                repos = self.current_repos
            options = self._get_options()
            self.backend.reset()                    # close the backend
            self.queue.queue.clear()                # clear the pending action queue
            self.queue.refresh()                    # clear the pending action queue
            self.populate_package_cache(repos=repos, show_dupes=self.show_dupes) # repopulate the package cache
            self.groups_is_loaded = False
            self.history_is_loaded = False
#            self.setup_groups()
#            self.setup_history(limit=self.settings.history_limit)
            self.notebook.set_active("package")     # show the package page
            if not self.settings.update_only and not self.settings.search:
                self.ui.packageFilterBox.show()         # Show the filter selector
            self.ui.packageSearch.set_text('')      # Reset search entry
            self._set_options(options)
            if not self.settings.search:
                self.ui.packageRadioUpdates.clicked()   # Select the updates package filter
            return True
        except YumexBackendFatalError, e:
            progress = self.get_progress()
            progress.hide()
            self.handle_error(e.err, e.msg)
            return False

# History helpers from yum output.py

    def _history_uiactions(self, hpkgs):
        actions = set()
        count = 0
        for hpkg in hpkgs:
            st = hpkg.state
            if st == 'True-Install':
                st = 'Install'
            if st == 'Dep-Install': # Mask these at the higher levels
                st = 'Install'
            if st == 'Obsoleted': 
                st = 'Obsoleting'
            if st in ('Install', 'Update', 'Erase', 'Reinstall', 'Downgrade',
                      'Obsoleting'):
                actions.add(st)
                count += 1
        assert len(actions) <= 6
        if len(actions) > 1:
            return count, ", ".join([x[0] for x in sorted(actions)])

        # So empty transactions work, although that "shouldn't" really happen
        return count, "".join(list(actions))


    def _pwd_ui_username(self, uid, limit=None):
        # loginuid is set to -1 on init.
        if uid is None or uid == 0xFFFFFFFF:
            loginid = _("<unset>")
            name = _("System") + " " + loginid
            if limit is not None and len(name) > limit:
                name = loginid
            return name

        try:
            user = pwd.getpwuid(uid)
            fullname = user.pw_gecos.split(';', 2)[0]
            name = "%s <%s>" % (fullname, user.pw_name)
            if limit is not None and len(name) > limit:
                name = "%s ... <%s>" % (fullname.split()[0], user.pw_name)
                if len(name) > limit:
                    name = "<%s>" % user.pw_name
            return name
        except KeyError:
            return str(uid)
        
    def _get_history_info(self, tids, limit=None):        
        data = []
        num_elem = 0
        for tid in tids:
            self.refresh()
            name = self._pwd_ui_username(tid.loginuid, 22)
            tm = time.strftime("%Y-%m-%d %H:%M",
                           time.localtime(tid.beg_timestamp))
            pkgs = self.backend.get_history_packages(tid.tid)
            num, uiacts = self._history_uiactions(pkgs)
            data.append([tid.tid, name, tm, uiacts, num])
            num_elem +=1
            if limit and num_elem > limit: # Show only a limited number of history elements (SPEED)
                break
        return data
    
    def setup_history(self, limit = None, force = False):       
        if not self.history_is_loaded or force:
 
            self.debug("Getting History Information - BEGIN")
            tids = self.backend.get_history()
            progress = self.get_progress()
            if limit == None:
                limit = self.settings.history_limit
            if tids:
                progress.set_pulse(True)
                progress.set_title(_("Getting History Information"))
                if limit != False:
                    progress.set_header(_("Getting Latest History Information"))
                else:
                    progress.set_header(_("Getting All History Information"))
    
                progress.show()
                data = self._get_history_info(tids, limit)
                self.history.populate(data)
            else:
                self.info(_("History Disabled"))
            progress.hide()
            self.debug("Getting History Information - END")
            self.history_is_loaded = True

    def search_history(self, pattern):       
        self.debug("Searching History Information - BEGIN")
        tids = self.backend.search_history(pattern)
        progress = self.get_progress()
        if tids:
            progress.set_pulse(True)
            progress.set_title(_("Searching History Information"))
            progress.set_header(_("Searching History Information"))
            progress.show()
            data = self._get_history_info(tids)
            self.history.populate(data)
        else:
            self.info(_("History Disabled"))
        progress.hide()
        self.debug("Searching History Information - END")

    def _order_packages(self, pkgs):
        if pkgs[0].state in HISTORY_NEW_STATES:
            tup = (pkgs[1],pkgs[0])
            state = pkgs[0].state
        else:    
            tup = (pkgs[0],pkgs[1])
            state = pkgs[1].state
        return tup,state
    
    def _get_relations(self, data):
        names = {}
        for hpo in data:
            if hpo.name in names:
                names[hpo.name].append(hpo)
            else:
                names[hpo.name] = [hpo]
        relations = {}
        for name in sorted(names.keys()):
            pkgs = names[name]
            if len(pkgs) != 2:
                self.info("no releation found: "+str([p.name+":"+p.ver+p.rel+":"+p.state for p in pkgs]))
                continue
            tup, state = self._order_packages(pkgs)
            if state in relations:                
                relations[state].append(tup)    
            else:
                relations[state] = [tup]    
        return relations
            

    def show_history_packages(self,tid):
        main = {}
        secondary = {}
        pkgs = self.backend.get_history_packages(tid, 'trans_with')
        secondary[_('Transaction Performed with')] = pkgs
        pkgs = self.backend.get_history_packages(tid, 'trans_skip')
        if pkgs:
            secondary[_('Skipped packages')] = pkgs
        pkgs = self.backend.get_history_packages(tid)
        values = {}
        for pkg in pkgs:
            if pkg.state in values:
                values[pkg.state].append(pkg)
            else:
                values[pkg.state] = [pkg]
        packages = {}                
        data = []
        for state in HISTORY_UPDATE_STATES:
            if state in values:
                data.extend(values[state])
        relations = self._get_relations(data)  
        for state in HISTORY_SORT_ORDER:
            if state in relations:
                main[state] = relations[state]
            elif state in values:
                main[state] = values[state]
        self.history_pkg_view.populate(main, secondary)
        
