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

from datetime import date

from yumexgui.gui import UI, Controller, Notebook, TextViewConsole, doGtkEvents
from yumexgui.progress import Progress
from yumexbase import *

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

    def error(self, msg):
        ''' Write an error message to frontend '''
        print "Error:",msg
        sys.exit(1)
        self.refresh()

    def warning(self, msg):
        ''' Write an warning message to frontend '''
        print "Warning:",msg
        self.output.write('WARNING: %s' % msg)
        self.refresh()

    def info(self, msg):
        ''' Write an info message to frontend '''
        print "INFO:",msg
        self.output.write(msg,style=self.output.style_out)
        self.refresh()

    def debug(self, msg):
        ''' Write an debug message to frontend '''
        print "DEBUG:",msg
        self.output.write('DEBUG: %s' % msg)
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
        # Create and ui object contains the widgets.
        ui = UI(BUILDER_FILE , 'main', 'yumex')
        # init the Controller Class to connect signals.
        Controller.__init__(self, ui)
        self.setup_gui()
        
# helpers
    def setup_gui(self):
        self.window = self.ui.main
        self.window.connect( "delete_event", self.quit )
        self.window.set_title("Yum Extender NextGen")
        self.output = TextViewConsole(self.ui.outputText)
        self.progress = Progress(self.ui,self.window)
        self.notebook = Notebook(self.ui.mainNotebook,self.ui.MainLeftContent)
        self.notebook.add_page("package","Packages",self.ui.packageMain, icon=PIXMAPS_PATH+'/button-packages.png')
        self.notebook.add_page("group","Groups",self.ui.groupMain, icon=PIXMAPS_PATH+'/button-group.png')
        self.notebook.add_page("repo","Repositories",self.ui.repoMain, icon=PIXMAPS_PATH+'/button-repo.png')
        self.notebook.add_page("queue","Action Queue",self.ui.queueMain, icon=PIXMAPS_PATH+'/button-queue.png')
        self.notebook.add_page("output","Output",self.ui.outputMain, icon=PIXMAPS_PATH+'/button-output.png')
        self.notebook.set_active("package")
        self.window.show()

# Signal handlers
      
    def quit(self, widget=None, event=None ):
        ''' Main destroy Handler '''
        gtk.main_quit()

    # Menu
        
    def on_fileQuit_activate(self, widget=None, event=None ):
        self.debug("File -> Quit")
        self.quit()

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
        self.debug("Package Search : %s" % self.ui.packageSearch.get_text())

    def on_packageClear_clicked(self, widget=None, event=None ):
        self.debug("Package Clear")
        self.ui.packageSearch.set_text('')

    def on_packageSelectAll_clicked(self, widget=None, event=None ):
        self.debug("Package Select All")

    def on_packageRedo_clicked(self, widget=None, event=None ):
        self.debug("Package Redo")

    # Repo Page    
        
    def on_repoOK_clicked(self, widget=None, event=None ):
        self.debug("Repo OK")
        
    def on_repoCancel_clicked(self, widget=None, event=None ):
        self.debug("Repo Cancel")

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
        self.debug("Progress Cansel")
                

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
        # setup
        self.backend.setup()
        # get_packages
        self.progress.show()
        self.progress.set_header("Testing Yum Backend")
        self.progress.set_label("Getting Updated Packages")
        pkgs = self.backend.get_packages(FILTER.updates)
        show(pkgs,True)
        self.progress.set_label("Getting Available Packages")
        pkgs = self.backend.get_packages(FILTER.available)
        show(pkgs)
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
        # search
        self.backend.search(['dummy'],SEARCH.name)        
        # reset        
        self.progress.hide()
        self.backend.reset()
        