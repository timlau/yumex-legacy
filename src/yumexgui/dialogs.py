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

from guihelpers import busyCursor, normalCursor, doGtkEvents
from yumexbase import YumexProgressBase
from yumexbase.constants import *
from yumexgui.views import YumexSearchOptionsView

# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
import logging
from yumexbase import _, P_
# pylint: enable-msg=W0611

class TaskList:
    '''
    A Task based progress list to show in a gtk.VBox widget
    
    tasks = TaskList(container,parent_window)
    tasks.add_task('task1','This is task 1')
    tasks.add_task('task2','This is task 2')
    tasks.add_task('task3','This is task 3')
    
    tasks.run_current() # task1 is now running
    tasks.show()
    # Do the action for task1
    tasks.next()  # task 2 is now running
    # Do the action for task2
    tasks.next()  # task 3 is now running
    # Do the action for task3
    tasks.complete_current() # task3 is complete
    tasks.hide()
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
        self.extra_label = ""
        self.hide()
        
    def __len__(self):
        return len(self._tasks)        

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
        task_label.set_size_request(400, -1)
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

    def next(self, task_id=None):
        '''
        Complete the current task and set the next to running
        if a task_id is given, all task before this task will be completed too
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

    def get_task_label(self, task_id = None):
        '''
        get the task label
        @param task_id:
        '''
        if task_id == None: # get current task
           task_id = self._task_no[self.num_current]
        if task_id in self._tasks:
            (state, icon, task_label, extra_label) = self._get_task(task_id)
            return task_label.get_text()

    def set_extra_label(self, task_id, text):
        '''
        set the task extra label
        @param task_id:
        @param text:
        '''
        self.extra_label = text
        if task_id in self._tasks:
            (state, icon, task_label, extra_label) = self._get_task(task_id)
            extra_label.set_markup(text)



class Progress(YumexProgressBase):
    '''
    The Progress Dialog
    '''

    def __init__(self, frontend):
        '''
        Setup the progress dialog
        @param ui: the UI class containing the dialog
        @param parent: the parent window widget
        '''
        YumexProgressBase.__init__(self)
        self.frontend = frontend
        self.ui = frontend.ui
        self.dialog = self.ui.Progress
        self.dialog.set_title("Working....")
        self.parent = frontend.window
        self.dialog.set_transient_for(self.parent)
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
        self.show_cancel(False) # Hide the Cancel button
        self.default_w = None
        self.default_h = None
        self._extra_widget = None
        self._active = False
        self.ui.progressImage.set_from_file(ICON_SPINNER)
        self.resize() # Setup the initial size
        self.extra_hidden = True
        self.task_hidden = True
        self.progress_hidden = False
        
    def close(self):
        self.dialog.hide()
        self.dialog.destroy()    

    def is_active(self):
        return self._active

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

    def resize(self):
        if not self.default_w: # store the default dialog size
            self.default_w, self.default_h = self.dialog.get_size()
        else:
            # Shrink dialog to the default size
            self.dialog.resize(self.default_w, self.default_h)
            self.dialog.queue_draw()

    def hide(self):
        '''
        Hide the progress dialog
        '''
        self._active = False
        #normalCursor(self.parent)
        self.dialog.hide()
        normalCursor(self.parent)

    def show_tasks(self):
        '''
        Show the tasks in the progress dialog
        '''
        #TODO : Make it possible to Cancel, before showing a cancel button
        #self.show_cancel(True)
        self.hide_extra()
        self.show_progress()
        self.tasks.show()
        self.task_hidden = False

    def hide_tasks(self):
        '''
        Hide the tasks in the progress dialog
        '''
        self.show_cancel(False)
        self.tasks.hide()
        self.resize()
        self.task_hidden = True
        
    def show_progress(self):
        '''
        Show the progress bar
        '''
        self.hide_extra()
        self.ui.progressImage.set_from_file(ICON_SPINNER)
        self.ui.progressPB.show()
        self.resize()
        self.progress_hidden = False
        
    def hide_progress(self):
        '''
        Hide the progress bar
        '''
        self.ui.progressPB.hide()
        self.progress_hidden = True
        
    def show_extra(self, widget=None):
        '''
        Show the progress extra
        '''
        self.ui.progressExtras.show()
        self.hide_progress()
        self.hide_tasks()
        self.ui.progressImage.set_from_stock('gtk-dialog-question',  gtk.ICON_SIZE_DND)
        self.extra_hidden = False
        
    def hide_extra(self):
        '''
        Hide the progress extra
        '''
        self.ui.progressExtras.hide()
        self.resize()
        self.extra_hidden = True

    def show_cancel(self, state=True):
        if state:
            self.ui.progressAction.show()
        else:
            self.ui.progressAction.hide()


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

class PrefBoolean(gtk.HBox):
    def __init__(self, text):
        gtk.HBox.__init__(self)
        # Setup CheckButton
        self._checkbutton = gtk.CheckButton(text)
        self._checkbutton.get_children()[0].modify_font(SMALL_FONT)
        self._checkbutton.set_alignment(0.0, 0.5)
        #self._checkbutton.set_padding(5, 0)
        self.pack_start(self._checkbutton, expand=False, padding=5)
        self.show_all()

    def get_value(self):
        return self._checkbutton.get_active()

    def set_value(self, state):
        self._checkbutton.set_active(state)

class PrefInt(gtk.HBox):
    def __init__(self, text, width=10):
        gtk.HBox.__init__(self)
        self._label = gtk.Label(text)
        self._label.modify_font(SMALL_FONT)
        self._label.set_alignment(0.0, 0.5)
        self._label.set_padding(5, 0)
        self._entry = gtk.Entry()
        self._entry.modify_font(SMALL_FONT)
        self._entry.set_width_chars(width)
        self.pack_start(self._label, expand=False, padding=5)
        self.pack_end(self._entry, expand=False, padding=5)
        self.show_all()

    def get_value(self):
        return int(self._entry.get_text())

    def set_value(self, value):
        self._entry.set_text(str(value))

class PrefStr(PrefInt):
    def __init__(self, text, width=40):
        PrefInt.__init__(self, text, width)

    def get_value(self):
        return self._entry.get_text()

    def set_value(self, text):
        self._entry.set_text(text)

class Preferences:

    def __init__(self, ui, parent, cfg):
        '''
        Preference dialog handler
        @param ui:
        @param parent:
        @param cfg: YumexOptions class instance
        '''
        self.ui = ui
        self.cfg = cfg
        self.settings = cfg.conf_settings
        self.dialog = self.ui.preferences
        self.dialog.set_title(_("Preferences"))
        self.parent = parent
        self.dialog.set_transient_for(parent)
        self._options = {}
        self.setup_basic()
        self.setup_advanced()
        self.setup_yum()

    def setup_basic(self):
        '''
        setup the basic options
        '''
        vbox = self.ui.prefBasicVBox
        self._add_option(PrefBoolean, vbox, 'autorefresh', _('Load packages on launch'))
        self._add_option(PrefBoolean, vbox, 'use_sortable_view', _('Use sortable columns in package view (slower)'))
        self._add_option(PrefBoolean, vbox, 'typeahead_search', _('Typeahead search is active by default'))
        vbox.show_all()

    def setup_advanced(self):
        '''
        setup the advanced options
        '''
        vbox = self.ui.prefAdvVBox
        self._add_option(PrefBoolean, vbox, 'debug', _('Debug Mode'))
        self._add_option(PrefBoolean, vbox, 'disable_netcheck', _('Disable startup network check'))
        self._add_option(PrefBoolean, vbox, 'use_sudo', _('Run backend with sudo (need working sudo nopasswd config)'))
        self._add_option(PrefStr, vbox, 'color_install', _('Color (Installed)'))
        self._add_option(PrefStr, vbox, 'color_update', _('Color (Update)'))
        self._add_option(PrefStr, vbox, 'color_normal', _('Color (Available)'))
        vbox.show_all()

    def setup_yum(self):
        '''
        setup the yum releated options
        '''
        vbox = self.ui.prefYumVBox
        self._add_option(PrefBoolean, vbox, 'plugins', _('Enable Yum Plugins'))
        self._add_option(PrefStr, vbox, 'proxy', _('Proxy'))
        self._add_option(PrefInt, vbox, 'yumdebuglevel', _('Yum Debug Level'))
        vbox.show_all()

    def _add_option(self, obj, vbox, id, text):
        '''
        Add an boolean option (CheckButton)
        @param vbox: the option page VBox widget
        @param id: the settings id (to read to setting value from)
        @param text: the option description text
        '''
        opt = obj(text)
        vbox.pack_start(opt , expand=False, padding=5)
        self._options[id] = opt
        opt.set_value(getattr(self.settings, id))

    def _refresh(self):
        for id in self._options:
            opt = self._options[id]
            opt.set_value(getattr(self.settings, id))
            
                


    def run(self):
        '''
        run the dialog
        '''
        self.settings = self.cfg.conf_settings
        self._refresh()
        self.dialog.show_all()
        rc = self.dialog.run()
        if rc == 1: # OK, save the options
            for id in self._options:
                opt = self._options[id]
                setattr(self.settings, id, opt.get_value())
            self.cfg.save()
            self.cfg.reload()
        self.destroy()

    def destroy(self):
        '''
        hide the dialog
        '''
        self.dialog.hide()

class SearchOptions:
    '''
    Search Options Dialog
    '''
    def __init__(self, ui, parent, keys, default_keys):
        self.ui = ui
        self.dialog = ui.searchOptionDialog
        self.parent = parent
        self.dialog.set_transient_for(self.parent)
        self.view = YumexSearchOptionsView(self.ui.searchOptionView)
        self.view.populate(keys, default_keys)

    def run(self):
        self.dialog.run()
        self.dialog.hide()

    def get_filters(self):
        return self.view.get_selected()

class TransactionConfirmation:
    '''
    The Transaction Confirmation dialog, to validate the result of the current transaction result
    '''

    def __init__(self, ui, progress):
        '''
        Init the dialog   
        @param ui: the UI class instance
        @param parent: the parent window widget
        '''
        self.ui = ui
        self.progress = progress
        self.view = self.ui.transactionView
        self.view.modify_font(SMALL_FONT)
        style = self.view.get_style()
        #self.ui.transactionEvent.modify_bg( gtk.STATE_NORMAL, style.base[0])        
        self.store = self.setup_view(self.view)
        self._active = False
        self.ui.transactionOK.connect("clicked", self.on_clicked,True)
        self.ui.transactionCancel.connect("clicked", self.on_clicked,False)
        self.hidden = None
        self.confirmation = None

    def on_clicked(self, widget, confirmation):
        self.confirmation = confirmation

    def is_active(self):
        return self._active

    def run(self):
        '''
        run the dialog
        '''
        self.hidden = (self.progress.progress_hidden, self.progress.task_hidden)
        self.progress.set_header(_("Transaction Result"))
        self.progress.show_extra()        
        self.view.expand_all()
        self._active = True
        self.confirmation = None
        while self.confirmation == None:
            doGtkEvents()
            time.sleep(0.01)
        return self.confirmation

    def destroy(self):
        '''
        hide the dialog
        '''
        self._active = False
        (progress_hidden, task_hidden) = self.hidden
        self.progress.hide_extra()
        if not progress_hidden:
            self.progress.show_progress()
        if not task_hidden:
            self.progress.show_tasks()

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
        self.create_text_column(_("Name"), view, 0, size=250)
        self.create_text_column(_("Arch"), view, 1)
        self.create_text_column(_("Ver"), view, 2)
        self.create_text_column(_("Repository"), view, 3)
        self.create_text_column(_("Size"), view, 4)
        return model

    def create_text_column(self, hdr, view, colno, size=None):
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
        if size:
            column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            column.set_fixed_width(size)
        view.append_column(column)


    def populate(self, pkglist, dnl_size):
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
        self.ui.transactionLabel.set_text(_("Download Size : %s ") % dnl_size)
        self.view.expand_all


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
        tag_table = self.longtext.get_buffer().get_tag_table()
        # make sure we only add the error tag once
        self.style_err = tag_table.lookup("error")
        if not self.style_err:
            self.style_err = gtk.TextTag("error")
            self.style_err.set_property("style", pango.STYLE_ITALIC)
            self.style_err.set_property("foreground", "red")
            self.style_err.set_property("family", "Monospace")
            self.style_err.set_property("size_points", 8)
            tag_table.add(self.style_err)

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
        buf.set_text('')
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

class TestWindow:
    """
    Test Window with Treeview, only used for testing of new views
    """

    def __init__(self, ui, backend, frontend):
        self.ui = ui
        self.backend = backend
        self.frontend = frontend
        self.window = self.ui.testWindow
        self.setup_gui()


    def setup_gui(self):
        self.window.show()


def okDialog(parent, msg):
    '''
    Open an OK message dialog
    @param parent: parrent window widget
    @param msg: dialog message
    '''
    dlg = gtk.MessageDialog(parent=parent,
                            type=gtk.MESSAGE_INFO,
                            buttons=gtk.BUTTONS_OK)
    dlg.set_title("Yum Extender")
    dlg.set_markup(cleanMarkupSting(msg))
    dlg.run()
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

def okCancelDialog(parent, msg):
    '''
    Open a Ok/Cancel message dialog
    @param parent: parent window widget
    @param msg: dialog message
    '''
    dlg = gtk.MessageDialog(parent=parent,
                            type=gtk.MESSAGE_QUESTION,
                            buttons=gtk.BUTTONS_OK_CANCEL)
    dlg.set_markup(cleanMarkupSting(msg))
    rc = dlg.run()
    dlg.destroy()
    if rc == gtk.RESPONSE_OK:
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
