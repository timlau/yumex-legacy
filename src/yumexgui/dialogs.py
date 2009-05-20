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
Yum Extender dialog classes and helper funtions
'''

import gtk
import pango
import gobject

from guihelpers import busyCursor, normalCursor
from yumexbase import YumexProgressBase
from yumexbase.constants import *
from guihelpers import doGtkEvents

# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
import logging
from yumexbase.i18n import _, P_
# pylint: enable-msg=W0611

class TaskList:
    '''
    '''
    
    def __init__(self, container, parent):
        '''
        Init the task list
        @param container: gtk.VBox widget to use as parent
        '''
        self.container = container
        self.parent = parent
        self._tasks = {}
        self._task_no = []
        self.num_tasks = 0
        self.num_current = 0
        self.is_hidden = True
        self.current_running = None
        self.hide()

    def show(self):
        '''
        show the tasklist
        '''
        self.is_hidden = False
        self.container.show_all()

    def hide(self):
        '''
        hide the tasklist
        '''
        self.is_hidden = True
        self.container.hide()
        self.reset()
        
    def reset(self):
        '''
        reset the task list by setting all tasks to TASK_PENDING
        '''
        for task_id in self._tasks:
            self._set_state(task_id, TASK_PENDING)
        self.num_current = 0
        
    def add_task(self, task_id, description):
        '''
        Add a new task to the list
        @param task_id:
        @param description:
        '''
        self._task_no.append(task_id)   
        self.num_tasks += 1
        hbox = gtk.HBox()
        icon = gtk.Image()
        icon.set_from_stock(TASK_ICONS[TASK_PENDING], gtk.ICON_SIZE_MENU)
        icon.set_size_request(25, 25)
        hbox.pack_start(icon, expand=False, fill=False, padding=0)
        sep = gtk.VSeparator()
        hbox.pack_start(sep, expand=False, fill=False, padding=0)
        task_label = gtk.Label(description)
        task_label.set_size_request(400, - 1)
        task_label.set_alignment(0.0, 0.5)
        task_label.set_padding(5, 0)
        hbox.pack_start(task_label, expand=False, fill=False, padding=0)
        extra_label = gtk.Label("")
        extra_label.modify_font(SMALL_FONT)
        hbox.pack_start(extra_label, expand=False, fill=False, padding=0)
        self.container.pack_start(hbox)
        self._set_task(task_id, TASK_PENDING, icon, task_label, extra_label)
        
    def run_current(self):       
        '''
        Run the current task
        ''' 
        cur = self._task_no[self.num_current] 
        self._set_state(cur, TASK_RUNNING)

    def complete_current(self):        
        '''
        Complete the current task
        '''
        cur = self._task_no[self.num_current] 
        self._set_state(cur, TASK_COMPLETE)
        return cur
    
    def next(self,task_id = None):
        '''
        Complete the current task and set the next to running
        if a task_id is given, all task before this task will be completted too
        @param task_id: Optional task_id to complete
        '''
        cur = None
        if not task_id:
            task_id = self._task_no[self.num_current]
        while task_id != cur:
            cur = self.complete_current()
            self.num_current += 1
        if self.num_current < self.num_tasks:
            self.run_current()
        
    def _set_task(self, task_id, state=None, icon=None, task_label=None, extra_label=None):
        '''
        set the task internals
        @param task_id:
        @param state:
        @param icon:
        @param task_label:
        @param extra_label:
        '''
        if task_id in self._tasks:
            cur_state, cur_icon, cur_task_label, cur_extra_label = self._get_task(task_id)
            if not state:
                state = cur_state
            if not icon:
                icon = cur_icon
            if not task_label:
                task_label = cur_task_label
            if not extra_label:
                extra_label = cur_extra_label
        if state and icon and task_label and extra_label:
            self._tasks[task_id] = (state, icon, task_label, extra_label)
        else:
            print "Error in _set_task(%s,%s,%s,%s)" % (state, icon, task_label, extra_label)

    def _get_task(self, task_id):
        '''
        get the task internals
        @param task_id:
        '''
        if task_id in self._tasks:
            return self._tasks[task_id]

    def _set_state(self, task_id, new_state):
        '''
        set task state (TASK_PENDING, TASK_RUNNING, TASK_COMPLETE"
        @param task_id:
        @param new_state:
        '''
        if task_id in self._tasks:
            (state, icon, task_label, extra_label) = self._get_task(task_id)
            if new_state == TASK_RUNNING:
                icon.set_from_file(ICON_SMALL_SPINNER)
            else:
                icon.set_from_stock(TASK_ICONS[new_state], gtk.ICON_SIZE_MENU)
            icon.show()
            self._set_task(task_id, state=new_state)
            if new_state == TASK_RUNNING:
                self.current_running = task_id
        else:
            print "Error in set_state(%s) task_id not definded"
            
    def set_task_label(self, task_id, text):
        '''
        set the task label
        @param task_id:
        @param text:
        '''
        if task_id in self._tasks:
            (state, icon, task_label, extra_label) = self._get_task(task_id)
            task_label.set_text(text)

    def set_extra_label(self, task_id, text):
        '''
        set the task extra label
        @param task_id:
        @param text:
        '''
        if task_id in self._tasks:
            (state, icon, task_label, extra_label) = self._get_task(task_id)
            extra_label.set_markup(text)    
            


class Progress(YumexProgressBase):
    '''
    The Progress Dialog
    '''
    
    def __init__(self, ui, parent):
        '''
        Setup the progress dialog
        @param ui: the UI class containing the dialog
        @param parent: the parent window widget
        '''
        YumexProgressBase.__init__(self)
        self.ui = ui
        self.dialog = self.ui.Progress
        self.dialog.set_title("Working....")
        self.parent = parent
        self.dialog.set_transient_for(parent)        
        style = self.ui.packageView.get_style()
        self.ui.progressEvent.modify_bg(gtk.STATE_NORMAL, style.base[0])        
        self.progressbar = self.ui.progressBar
        self.progressbar.modify_font(SMALL_FONT)
        self.header = self.ui.progressHeader
        self.header.modify_font(BIG_FONT)
        self.label = self.ui.progressLabel
        self.label.modify_font(SMALL_FONT)
        self.tasks = TaskList(self.ui.progressTasks, self.dialog)
        self.tasks.add_task('depsolve', _('Resolving Dependencies'))
        self.tasks.add_task('download', _("Downloading Packages"))
        self.tasks.add_task('gpg-check', _("Checking Package GPG Signatures"))
        self.tasks.add_task('test-trans', _("Running RPM Test Transaction"))
        self.tasks.add_task('run-trans', _("Running RPM Transaction"))
        self.tasks.hide()
        self.default_w = None
        self.default_h = None
        self.ui.progressImage.set_from_file(ICON_SPINNER)
        
    def show(self):
        '''
        Show the progress dialog
        '''
        self._active = True
        busyCursor(self.parent, True)
        self.reset()
        self.dialog.show()
        if not self.default_w: # store the default dialog size
            self.default_w, self.default_h = self.dialog.get_size()
        elif self.tasks.is_hidden:
            # Shrink dialog to the default size
            self.dialog.resize(self.default_w, self.default_h) 
            self.dialog.queue_draw()
            
            
        
    def hide(self):
        '''
        Hide the progress dialog
        '''
        self._active = False
        normalCursor(self.parent)
        self.dialog.hide()
        
    def show_tasks(self):
        '''
        Show the tasks in the progress dialog
        '''
        self.tasks.show()

    def hide_tasks(self):
        '''
        Hide the tasks in the progress dialog
        '''
        self.tasks.hide()
        
    def set_title(self, text):
        '''
        Set the title of the dialog
        @param text: the title to set
        '''
        self.dialog.set_title(text)
        
    def set_header(self, text):
        '''
        Set the dialog header text, it will also blank the action text
        @param text: The header text
        '''
        self.header.set_text(text)
        self.set_action("")
        
    def set_action(self, text):
        '''
        set the action text 
        @param text: the action text
        '''
        self.label.set_markup(text)
        
    def set_fraction(self, frac, text=None):
        '''
        Set the progress bar fraction and text
        @param frac: the progressbar fraction (0.0 -> 1.0)
        @param text: the progressbar text
        '''
        self.progressbar.set_fraction(frac)
        if text:
            self.progressbar.set_text(text)
            
    def pulse(self):
        '''
        Pulse the progressbar and set the text to Working (translated)
        '''
        self.progressbar.set_text(_("Working !!!"))
        self.progressbar.pulse()
        
    def reset(self):
        '''
        Reset the progressbar and progressbar text
        '''
        self.progressbar.set_fraction(0.0)
        self.progressbar.set_text("")
            
class TransactionConfirmation:
    '''
    The Transaction Confirmation dialog, to validate the result of the current transaction result
    '''
    
    def __init__(self, ui, parent):
        '''
        Init the dialog   
        @param ui: the UI class instance
        @param parent: the parent window widget
        '''
        self.ui = ui
        self.dialog = self.ui.Transaction
        self.dialog.set_title(_("Transaction Result"))
        self.parent = parent
        self.dialog.set_transient_for(parent)        
        self.view = self.ui.transactionView
        self.view.modify_font(SMALL_FONT)        
        style = self.view.get_style()
        #self.ui.transactionEvent.modify_bg( gtk.STATE_NORMAL, style.base[0])        
        self.header = self.ui.transactionHeader
        self.header.modify_font(BIG_FONT)
        self.set_header(_("Transaction Result"))
        self.store = self.setup_view(self.view)

    def run(self):
        '''
        run the dialog
        '''
        self.dialog.show_all()
        self.view.expand_all()
        rc = self.dialog.run()
        return rc == 1

    def destroy(self):
        '''
        hide the dialog
        '''
        self.dialog.hide()

        
    def set_header(self, text):
        '''
        The the header text
        @param text: the header text
        '''
        self.header.set_text(text)
        
    def setup_view(self, view):
        '''
        Setup the TreeView
        @param view: the TreeView widget
        '''
        model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
                              gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
        view.set_model(model)
        self.create_text_column(_("Name"), view, 0)
        self.create_text_column(_("Arch"), view, 1)
        self.create_text_column(_("Ver"), view, 2)
        self.create_text_column(_("Repository"), view, 3)
        self.create_text_column(_("Size"), view, 4)
        return model

    def create_text_column(self, hdr, view, colno, min_width=0):
        '''
        Create at TreeViewColumn 
        @param hdr: column header text
        @param view: the TreeView widget
        @param colno: the TreeStore column containing data for the column
        @param min_width: the min column view (optional)
        '''
        cell = gtk.CellRendererText()    # Size Column
        column = gtk.TreeViewColumn(hdr, cell, markup=colno)
        column.set_resizable(True)
        if not min_width == 0:
            column.set_min_width(min_width)
        view.append_column(column)        
             
             
    def populate(self, pkglist):
        '''
        Populate the TreeView with data
        @param pkglist: list containing view data 
        '''
        model = self.store
        self.store.clear()       
        for sub, lvl1 in pkglist:
            label = "<b>%s</b>" % sub
            level1 = model.append(None, [label, "", "", "", ""])
            for name, arch, ver, repo, size, replaces in lvl1:
                level2 = model.append(level1, [name, arch, ver, repo, size])
                for r in replaces:
                    level3 = model.append(level2, [ r, "", "", "", ""])


class ErrorDialog:
    '''
    The Error Message Dialog
    '''
    
    def __init__(self, ui, parent, title, text, longtext, modal):
        '''
        Setup the Error Message Dialog
        @param ui: the UI class
        @param parent: the parent window widget
        @param title: dialog title
        @param text: dialog header text
        @param longtext: dialog main text
        @param modal: is modal 
        '''
        self.ui = ui
        self.dialog = ui.errDialog
        self.parent = parent
        if parent:
            self.dialog.set_transient_for(parent)
        self.dialog.set_icon_name('gtk-dialog-error')
        self.dialog.set_title(title)
        self.text = self.ui.errText
        self.longtext = self.ui.errTextView
        self.style_err = gtk.TextTag("error") 
        self.style_err.set_property("style", pango.STYLE_ITALIC)
        self.style_err.set_property("foreground", "red")
        self.style_err.set_property("family", "Monospace")
        self.style_err.set_property("size_points", 8)
        self.longtext.get_buffer().get_tag_table().add(self.style_err)
        
        if modal:
            self.dialog.set_modal(True)
        if text != "":
            self.set_text(text)
        if longtext != "" and longtext != None:
            self.set_long_text(longtext)
        
    def set_text(self, text):
        '''
        Set the dialog header text
        @param text: the header text
        '''
        self.text.set_markup(text)
    
    def set_long_text(self, longtext):
        '''
        Set the main dialog text
        @param longtext: the main text
        '''
        buf = self.longtext.get_buffer()
        start, end = buf.get_bounds()
        buf.insert_with_tags(end, longtext, self.style_err)
        
    def run(self):
        '''
        Run the dialog
        '''
        self.dialog.show_all()
        return self.dialog.run()

    def destroy(self):
        '''
        Hide the dialog
        '''
        self.dialog.hide()

def okDialog(parent, msg):
    '''
    Open an OK message dialog
    @param parent: parrent window widget
    @param msg: dialog message
    '''
    dlg = gtk.MessageDialog(parent=parent,
                            type=gtk.MESSAGE_INFO,
                            buttons=gtk.BUTTONS_OK)
    dlg.set_markup(cleanMarkupSting(msg))
    rc = dlg.run()
    dlg.destroy()

def questionDialog(parent, msg):
    '''
    Open a Yes/No message dialog
    @param parent: parent window widget
    @param msg: dialog message
    '''
    dlg = gtk.MessageDialog(parent=parent,
                            type=gtk.MESSAGE_QUESTION,
                            buttons=gtk.BUTTONS_YES_NO)
    dlg.set_markup(cleanMarkupSting(msg))
    rc = dlg.run()
    dlg.destroy()
    if rc == gtk.RESPONSE_YES:
        return True
    else:
        return False
    
def cleanMarkupSting(msg):
    '''
    Make the sting legal to use as Markup 
    @param msg:
    '''
    msg = str(msg) # make sure it is a string
    msg = gobject.markup_escape_text(msg)
    return msg
            