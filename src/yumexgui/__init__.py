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

import sys
import gtk
import pango
import logging

from datetime import date

from yumexgui.gui import UI, Controller, Notebook, TextViewConsole, doGtkEvents, PackageCache,busyCursor,normalCursor
from yumexgui.progress import Progress
from yumexgui.views import YumexPackageView,YumexQueueView,YumexRepoView
from yumexbase import *
from yumexbase.i18n import _


class YumexFrontend(YumexFrontendBase):
    '''
    Yumex Frontend  class

    This is a frontend callback class used by the backend and
    transaction to notify the frontend about changes.
    '''

    def __init__(self, backend, progress):
        ''' Setup the frontend callbacks '''
        YumexFrontendBase.__init__(self, backend, progress)
        
    def set_state(self, state):
        ''' set the state of work '''
        pass

    def get_progress(self):
        ''' Get the current progress object '''
        return self._progress

    def progress(self):
        ''' trigger at progress update'''
        pass

    def confirm_transaction(self, transaction):
        ''' confirm the current transaction'''
        pass

    def error(self, msg, exit=False):
        ''' Write an error message to frontend '''
        self.output.write('ERROR: %s' % msg,'error')
        self.refresh()
        if exit:
            sys.exit(1)
            

    def warning(self, msg):
        ''' Write an warning message to frontend '''
        print "Warning:",msg
        self.output.write('WARNING: %s' % msg,'info')
        self.refresh()

    def info(self, msg):
        ''' Write an info message to frontend '''
        print "INFO:",msg
        self.output.write(msg,'info')
        self.refresh()

    def debug(self, msg):
        ''' Write an debug message to frontend '''
        print "DEBUG:",msg
        self.output.write('DEBUG: %s' % msg,"debug")
        self.refresh()

    def exception(self, msg):
        ''' handle an expection '''
        msg = msg.replace(";","\n")
        print "exception:",msg
        sys.exit(1)

    def reset(self):
        ''' trigger a frontend reset '''
        pass

    def timeout(self):
        self.refresh()
        
    def refresh(self):               
        if self.progress.is_active:
            self.progress.pulse()
        doGtkEvents()
        
class YumexHandlers(Controller):
    ''' This class contains all glade signal callbacks '''
    
    
    def __init__(self):
        # init the Controller Class to connect signals etc.
        Controller.__init__(self, BUILDER_FILE , 'main', 'yumex')
        self.package_cache = PackageCache(self.backend)
        self._last_filter = None
        self.setup_gui()
        
# helpers
    def setup_gui(self):
        # setup
        self.window.set_title("Yum Extender NextGen")
        self.output = TextViewConsole(self.ui.outputText)
        self.progress = Progress(self.ui,self.window)
        self.notebook = Notebook(self.ui.mainNotebook,self.ui.MainLeftContent)
        self.notebook.add_page("package","Packages",self.ui.packageMain, icon=PIXMAPS_PATH+'/button-packages.png')
        self.notebook.add_page("group","Groups",self.ui.groupMain, icon=PIXMAPS_PATH+'/button-group.png')
        self.notebook.add_page("repo","Repositories",self.ui.repoMain, icon=PIXMAPS_PATH+'/button-repo.png')
        self.notebook.add_page("queue","Pending Action Queue",self.ui.queueMain, icon=PIXMAPS_PATH+'/button-queue.png')
        self.notebook.add_page("output","Output",self.ui.outputMain, icon=PIXMAPS_PATH+'/button-output.png')
        self.notebook.set_active("package")
        self.queue = YumexQueueView(self.ui.queueView)
        self.packages = YumexPackageView(self.ui.packageView,self.queue)
        self.repos = YumexRepoView(self.ui.repoView)
        self.window.show()
        self.setup_filters()
        self.populate_package_cache()
        self.setup_repositories()
        # setup default package filter (updates)
        self.ui.packageFilter.set_active(0)

    def setup_filters(self):
        ''' Populate Package Filter Combobox'''
        model = gtk.ListStore( str )
        for flt in PKG_FILTERS_STRINGS:
            print flt
            model.append([flt])
        self.ui.packageFilter.set_model( model )
        label = self.ui.packageFilter.get_children()[0]
        label.modify_font(XSMALL_FONT)

    def setup_repositories(self):
        repos = self.backend.get_repositories()
        self.repos.populate(repos)
                
    def populate_package_cache(self):
        self.backend.setup()
        self.progress.show()
        self.progress.set_header("Getting Package Lists")
        self.progress.set_label("Getting Updated Packages")
        pkgs = self.package_cache.get_packages(FILTER.updates)
        self.progress.set_label("Getting Available Packages")
        pkgs = self.package_cache.get_packages(FILTER.available)
        self.progress.set_label("Getting installed Packages")
        pkgs = self.package_cache.get_packages(FILTER.installed)
        self.progress.hide()

        
        

# Signal handlers
      
    def quit(self, widget=None, event=None ):
        ''' destroy Handler '''
        self.backend.reset()

    # Menu
        
    def on_fileQuit_activate(self, widget=None, event=None ):
        self.debug("File -> Quit")
        self.main_quit()

    def on_editPref_activate(self, widget=None, event=None ):
        self.debug("Edit -> Preferences")

    def on_proNew_activate(self, widget=None, event=None ):
        self.debug("Profiles -> New")

    def on_proSave_activate(self, widget=None, event=None ):
        self.debug("Profiles -> Save")
        
    def on_helpAbout_activate(self, widget=None, event=None ):
        self.debug("Help -> About")

    # Package Page    
        
    def on_packageSearch_activate(self, widget=None, event=None ):
        busyCursor(self.window)
        active = self.ui.packageFilter.get_active()
        if active != -1:
            self._last_filter = active
        filters = ['name','summary']
        keys = self.ui.packageSearch.get_text().split(' ')
        pkgs = self.backend.search(keys,filters)
        self.ui.packageFilter.set_active(-1)            
        self.packages.add_packages(pkgs)
        normalCursor(self.window)
        

    def on_packageClear_clicked(self, widget=None, event=None ):
        self.debug("Package Clear")
        self.ui.packageSearch.set_text('')
        if self._last_filter != -1:
            self.ui.packageFilter.set_active(self._last_filter)            
            

    def on_packageSelectAll_clicked(self, widget=None, event=None ):
        self.packages.selectAll()

    def on_packageRedo_clicked(self, widget=None, event=None ):
        self.packages.deselectAll()

    def on_packageFilter_changed(self, widget=None, event=None ):
        active = self.ui.packageFilter.get_active()
        if active == -1:
            return
        busyCursor(self.window)
        self.ui.packageSearch.set_text('')        
        self.backend.setup()
        pkgs = self.package_cache.get_packages(PKG_FILTERS_ENUMS[active])
        action = ACTIONS[active]
        self.packages.add_packages(pkgs,progress = self.progress)
        normalCursor(self.window)
            
    # Repo Page    
        
    def on_repoOK_clicked(self, widget=None, event=None ):
        self.debug("Repo OK")
        
    def on_repoUndo_clicked(self, widget=None, event=None ):
        self.debug("Repo Undo")

    # Queue Page    

    def on_queueOpen_clicked(self, widget=None, event=None ):
        self.debug("Queue Open")
    
    def on_queueSave_clicked(self, widget=None, event=None ):
        self.debug("Queue Save")
    
    def on_queueRemove_clicked(self, widget=None, event=None ):
        self.debug("Queue Remove")

    def on_Execute_clicked(self, widget=None, event=None ):
        self.debug("Queue Execute ")
        self.notebook.set_active("output")
        self.run_test()
        
    def on_progressCancel_clicked(self, widget=None, event=None ):
        self.debug("Progress Cancel : "+event)
                

class YumexApplication(YumexHandlers, YumexFrontend):
    """
    The Yum Extender main application class 
    """
    
    def __init__(self,backend):
        self.backend = backend(self)
        self.progress = None
        self.setup_backend()
        YumexHandlers.__init__(self)
        YumexFrontend.__init__(self, self.backend, self.progress)
    
    def setup_backend(self):
        #TODO: Add some reel backend setup code
        self.progress = None
        
    def run(self):
        # setup
        self.backend.setup()
        gtk.main()        
        
    def run_test(self):
        def show(elems,desc=False):
            if elems:
                i = 0
                for el in elems:
                    i += 1
                    self.info("  %s" % str(el))
                    if desc:
                        self.info(el.description)
                    if i == 20:
                        break
        # get_packages
        self.progress.show()
        self.progress.set_header("Testing Yum Backend")
        self.progress.set_label("Getting Updated Packages")
        pkgs = self.backend.get_packages(FILTER.updates)
        #show(pkgs,True)
        self.progress.set_label("Getting Available Packages")
        pkgs = self.backend.get_packages(FILTER.available)
        #show(pkgs)
        for po in pkgs:
            if po.name == 'kdegames':
                break
        self.progress.set_label("Showing Filelist")
        self.info("Package : %s\n" % str(po))
        self.info("\nFiles:")
        i = 0
        for f in po.filelist:
            i += 1
            self.info("  %s" % f.strip('\n'))
            if i == 20: break
        num = 0    
        self.progress.set_label("Showing Changelog")
        self.info("\nChangelog")
        for (d,a,msg) in po.changelog:
            num += 1
            self.info(" %s %s" % (date.fromtimestamp(d).isoformat(),a))
            for line in msg.split('\n'):
                self.info("  %s" % line)
            if num == 3: break
        print    
        # Add to transaction for install
        self.backend.transaction.add(po,'install')
        tpkgs = self.backend.transaction.get_transaction_packages()
        show(tpkgs)
        # get_groups
        grps = self.backend.get_groups()
        show(grps)
        self.progress.set_label("Getting Repository information")
        # get_repositories
        repos = self.backend.get_repositories()
        for repo in repos:
            id,name,enabled,gpgckeck = repo
            self.info("%-50s : %s" % (id,enabled))
        # enable_repository
        repo = self.backend.enable_repository('updates',False)
        id,name,enabled,gpgckeck = repo
        self.info("%-50s : %s" % (id,enabled))        
        self.progress.hide()
        