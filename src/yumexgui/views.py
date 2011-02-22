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
Yum Extender GUI View classes
'''


import gtk
import gobject
import logging
import os
import time

from yumexbase import _, P_
from yumexbase import TimeFunction
import yumexbase.constants as const
from guihelpers import  doGtkEvents, busyCursor, normalCursor


from yum.misc import sortPkgObj

class SelectionView:
    '''
    A Base view with an selection column
    '''

    def __init__(self, widget):
        '''
        init the view
        @param widget: the gtk TreeView widget
        '''
        self.view = widget
        self.store = None

    def create_text_column_num(self, hdr, colno, resize=True, size=None, markup=False):
        '''
        Create a TreeViewColumn with data from a TreeStore column
        @param hdr: column header text
        @param colno: TreeStore column to get the data from
        @param resize: is resizable
        '''
        cell = gtk.CellRendererText()
        if markup:
            column = gtk.TreeViewColumn(hdr, cell, markup=colno)
        else:
            column = gtk.TreeViewColumn(hdr, cell, text=colno)
        column.set_resizable(resize)
        if size:
            column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            column.set_fixed_width(size)
        self.view.append_column(column)
        return column

    def create_text_column(self, hdr, prop, size, sortcol=None):
        """ 
        Create a TreeViewColumn with text and set
        the sorting properties and add it to the view
        """
        cell = gtk.CellRendererText()    # Size Column
        column = gtk.TreeViewColumn(hdr, cell)
        column.set_resizable(True)
        column.set_cell_data_func(cell, self.get_data_text, prop)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(size)
        if sortcol:
            column.set_sort_column_id(sortcol)
            #column.set_sort_indicator(True)
            #column.set_sort_order(gtk.SORT_ASCENDING)       
        else:
            column.set_sort_column_id(-1)
        self.view.append_column(column)
        return column

    def create_selection_colunm(self, attr):
        '''
        Create an selection column, there get data via property function and a key attr
        @param attr: key attr for property funtion
        '''
        # Setup a selection column using a object attribute 
        cell1 = gtk.CellRendererToggle()    # Selection
        cell1.set_property('activatable', True)
        column1 = gtk.TreeViewColumn("", cell1)
        column1.set_cell_data_func(cell1, self.get_data_bool, attr)
        column1.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column1.set_fixed_width(20)
        column1.set_sort_column_id(-1)
        self.view.append_column(column1)
        cell1.connect("toggled", self.on_toggled)
        column1.set_clickable(True)

    def create_selection_column_num(self, num, data_func=None):
        '''
        Create an selection column, there get data an TreeStore Column        
        @param num: TreeStore column to get data from
        '''
        # Setup a selection column using a column num

        column = gtk.TreeViewColumn(None, None)
        # Selection checkbox
        selection = gtk.CellRendererToggle()    # Selection
        selection.set_property('activatable', True)
        column.pack_start(selection, False)
        if data_func:
            column.set_cell_data_func(selection, data_func)
        else:
            column.add_attribute(selection, "active", num)
        column.set_resizable(True)
        column.set_sort_column_id(-1)
        self.view.append_column(column)
        selection.connect("toggled", self.on_toggled)
        return column

    def create_selection_text_column(self, hdr, select_func, text_attr, size=200):
        '''
        Create an selection column, there get data an TreeStore Column        
        @param num: TreeStore column to get data from
        '''
        # Setup a selection column using a column num

        column = gtk.TreeViewColumn(hdr, None)
        # Selection checkbox
        selection = gtk.CellRendererToggle()    # Selection
        selection.set_property('activatable', True)
        selection.connect("toggled", self.on_toggled)
        column.pack_start(selection, False)
        column.set_cell_data_func(selection, select_func)
        text = gtk.CellRendererText()
        column.pack_start(text, False)
        column.set_cell_data_func(text, self.get_data_text, text_attr)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(size)
        column.set_sort_column_id(-1)
        self.view.append_column(column)
        return column

    def get_data_text(self, column, cell, model, iterator, prop):
        '''
        a property function to get string data from a object in the TreeStore based on
        an attributes key
        @param column:
        @param cell:
        @param model:
        @param iterator:
        @param prop: attribute key
        '''
        obj = model.get_value(iterator, 0)
        if obj:
            cell.set_property('text', getattr(obj, prop))
            cell.set_property('foreground', obj.color)

    def get_data_bool(self, column, cell, model, iterator, prop):
        '''
        a property function to get boolean data from a object in the TreeStore based on
        an attributes key
        
        @param column:
        @param cell:
        @param model:
        @param iterator:
        @param prop: attribute key
        '''
        obj = model.get_value(iterator, 0)
        cell.set_property("visible", True)
        if obj:
            cell.set_property("active", getattr(obj, prop))


    def on_toggled(self, widget, path):
        ''' 
        selection togged handler
        overload in child class
        '''
        pass

class YumexPackageBase(SelectionView):

    def __init__(self, widget, qview, frontend):
        '''
        Init the view
        @param widget: the gtk TreeView widget
        @param qview: the queue view instance to use for queuing
        '''
        SelectionView.__init__(self, widget)
        self.view.modify_font(const.SMALL_FONT)
        self.headers = [_("Package"), _("Ver"), _("Summary"), _("Repo"), _("Architecture"), _("Size")]
        self.store = self.setupView()
        self.queue = qview.queue
        self.queueView = qview
        self.frontend = frontend

    def setupView(self):
        '''
        Setup the TreeView
        '''
        raise NotImplementedError

    def on_toggled(self, widget, path):
        """ Package selection handler """
        iterator = self.store.get_iter(path)
        obj = self.store.get_value(iterator, 0)
        self.togglePackage(obj)
        self.queueView.refresh()

    def togglePackage(self, obj):
        '''
        Toggle the package queue status
        @param obj:
        '''
        if obj.queued == obj.action:
            obj.queued = None
            self.queue.remove(obj)
            obj.set_select(not obj.selected)
        elif not self.queue.has_pkg_with_name_arch(obj):
            obj.queued = obj.action
            self.queue.add(obj)
            obj.set_select(not obj.selected)

    def selectAll(self):
        '''
        Select all packages in the view
        '''
        for el in self.store:
            obj = el[0]
            if not obj.queued == obj.action:
                obj.queued = obj.action
                self.queue.add(obj)
                obj.set_select(not obj.selected)
        self.queueView.refresh()
        self.view.queue_draw()

    def deselectAll(self):
        '''
        Deselect all packages in the view
        '''
        for el in self.store:
            obj = el[0]
            if obj.queued == obj.action:
                obj.queued = None
                self.queue.remove(obj)
                obj.set_select(not obj.selected)
        self.queueView.refresh()
        self.view.queue_draw()

    def new_pixbuf(self, column, cell, model, iterator):
        """ 
        Cell Data function for recent Column, shows pixmap
        if recent Value is True.
        """
        pkg = model.get_value(iterator, 0)
        if pkg:
            action = pkg.queued
            if action:
                if action in ('u', 'i', 'o'):
                    icon = 'network-server'
                elif action == 'ri':
                    icon = 'gtk-refresh'
                elif action == 'do':
                    icon = 'gtk-go-down'
                else:
                    icon = 'edit-delete'
                cell.set_property('visible', True)
                cell.set_property('icon-name', icon)
            else:
                cell.set_property('visible', pkg.recent)
                cell.set_property('icon-name', 'document-new')
        else:
            cell.set_property('visible', False)


    def get_selected(self, package=True):
        """ Get selected packages in current packageList """
        selected = []
        for row in self.store:
            col = row[0]
            if col:
                pkg = row[0][0]
                if pkg.selected:
                    selected.append(pkg)
        return selected

    def clear(self):
        '''
        Clear the view
        '''
        self.store.clear()

    def doGtkEvents(self):
        '''
        
        '''
        i = 0
        progress = self.frontend.get_progress()
        while gtk.events_pending():      # process gtk events
            i += 1
            if (i % 5) == 0:
                if progress:
                    progress.pulse()
            gtk.main_iteration()


class YumexPackageView(YumexPackageBase):
    '''
    Yum Extender Package View
    '''

    def __init__(self, widget, qview, frontend):
        '''
        Init the view
        @param widget: the gtk TreeView widget
        @param qview: the queue view instance to use for queuing
        '''
        YumexPackageBase.__init__(self, widget, qview, frontend)

    def setupView(self):
        '''
        Setup the TreeView
        '''
        store = gtk.ListStore(gobject.TYPE_PYOBJECT, str)
        self.view.set_model(store)
        self.create_selection_colunm('selected')
        # Setup resent column
        cell2 = gtk.CellRendererPixbuf()    # new
        cell2.set_property('stock-id', gtk.STOCK_ADD)
        column2 = gtk.TreeViewColumn("", cell2)
        column2.set_cell_data_func(cell2, self.new_pixbuf)
        column2.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column2.set_fixed_width(20)
        column2.set_sort_column_id(-1)
        self.view.append_column(column2)
        column2.set_clickable(True)

        self.create_text_column(_("Package"), 'name' , size=200)
        self.create_text_column(_("Ver."), 'fullver', size=120)
        self.create_text_column(_("Arch."), 'arch' , size=60)
        self.create_text_column(_("Summary"), 'summary', size=400)
        self.create_text_column(_("Repo."), 'repoid' , size=90)
        self.create_text_column(_("Size."), 'size' , size=90)
        self.view.set_search_column(1)
        self.view.set_enable_search(True)
        #store.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.view.set_reorderable(False)
        return store


    #@TimeFunction
    def add_packages(self, pkgs):
        '''
        Populate the via with package objects
        @param pkgs: list of package object to add
        @param progress:
        '''
        self.store.clear()
        queued = self.queue.get()
        if pkgs:
            pkgs.sort(sortPkgObj)
            self.frontend.debug("Starting package view population")
            start = time.time()
            self.view.freeze_child_notify()
            self.view.set_model(None)
            for po in pkgs:
                self.store.append([po, str(po)])
                if po in queued[po.action]:
                    po.queued = po.action
                    po.set_select(True)
            self.view.set_model(self.store)
            self.view.thaw_child_notify()
            self.doGtkEvents()
            end = time.time()
            self.frontend.debug("Ended package view population. time : %.2f " % (end - start))


#    def add_packages(self, pkgs, progress=None):
#        '''
#        Populate the via with package objects
#        @param pkgs: list of package object to add
#        @param progress:
#        '''
#        self.store.clear()
#        queued = self.queue.get()
#        if pkgs:
#            pkgs.sort(sortPkgObj)
#            loader = self.fill_tree(pkgs)
#            #gobject.idle_add(loader.next)
#            gobject.timeout_add(20, loader.next)


    def fill_tree(self, pkgs, step=20):
        '''Generator to fill the listmodel of a treeview progressively.'''
        print "Starting population"
        start = time.time()
        n = 0
        queued = self.queue.get()

        self.view.freeze_child_notify()
        for po in pkgs:
            self.store.append([po, str(po)])
            if po in queued[po.action]:
                po.queued = po.action
                po.set_select(True)

            # yield to gtk main loop once awhile
            n += 1
            if (n % step) == 0:
                self.view.thaw_child_notify()
                yield True
                self.view.freeze_child_notify()

        self.view.thaw_child_notify()
        # stop idle_add()
        end = time.time()
        print "Ending population : %.2f " % (end - start)
        yield False



class YumexPackageViewSorted(YumexPackageBase):
    '''
    Yum Extender Package View
    '''

    def __init__(self, widget, qview, frontend):
        '''
        Init the view
        @param widget: the gtk TreeView widget
        @param qview: the queue view instance to use for queuing
        '''
        YumexPackageBase.__init__(self, widget, qview, frontend)

    def setupView(self):
        '''
        Setup the TreeView
        '''
        store = gtk.ListStore(gobject.TYPE_PYOBJECT, str, str, str, str, str, long)
        self.sort_store = gtk.TreeModelSort(store)

        self.view.set_model(self.sort_store)
        self.create_selection_colunm('selected')
        # Setup resent column
        cell2 = gtk.CellRendererPixbuf()    # new
        cell2.set_property('stock-id', gtk.STOCK_ADD)
        column2 = gtk.TreeViewColumn("", cell2)
        column2.set_cell_data_func(cell2, self.new_pixbuf)
        column2.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column2.set_fixed_width(20)
        column2.set_sort_column_id(-1)
        self.view.append_column(column2)
        column2.set_clickable(True)

        self.create_text_column(_("Package"), 'name' , size=200, sortcol=1)
        self.create_text_column(_("Ver."), 'fullver', size=120, sortcol=2)
        self.create_text_column(_("Arch."), 'arch' , size=60, sortcol=3)
        self.create_text_column(_("Summary"), 'summary', size=400, sortcol=4)
        self.create_text_column(_("Repo."), 'repoid' , size=90, sortcol=5)
        self.create_text_column(_("Size."), 'size' , size=90, sortcol=6)
        #self.view.set_search_column(1)
        #self.view.set_enable_search(True)
        self.sort_store.set_sort_column_id(1, gtk.SORT_ASCENDING)
        self.view.set_reorderable(False)
        return store

    #@TimeFunction
    def add_packages(self, pkgs):
        '''
        Populate the via with package objects
        @param pkgs: list of package object to add
        @param progress:
        '''
        self.store.clear()
        queued = self.queue.get()
        if pkgs:
            self.frontend.debug("Starting package view population - sorted view")
            start = time.time()
            pkgs.sort(sortPkgObj)
            #self.view.freeze_child_notify()
            self.view.set_model(None)
            del self.store
            self.store = gtk.ListStore(gobject.TYPE_PYOBJECT, str, str, str, str, str, long)
            self.sort_store = gtk.TreeModelSort(self.store)
            self.frontend.debug("package view population - start adding to store")

            i = 0
            for po in pkgs:
                # bump the progress bar
                i += 1
                if (i % 200) == 0: # Refresh gui + progressbar
                    self.frontend.refresh()
                self.store.append([po, po.fullname, po.fullver, po.arch, po.summary, po.repoid, po.sizeBytes])
                if po in queued[po.action]:
                    po.queued = po.action
                    po.set_select(True)
            self.frontend.debug("package view population - end adding to store")
            self.sort_store.set_sort_column_id(1, gtk.SORT_ASCENDING)
            self.frontend.debug("package view population - sort column set")
            self.view.set_model(self.sort_store)
            self.frontend.debug("package view population - store is applied to TreeView")
            #self.view.thaw_child_notify()            
            self.frontend.debug("package view population - start GtkEvent Processing")
            self.doGtkEvents()
            self.frontend.debug("package view population - end GtkEvent Processing")

    def on_toggled(self, widget, spath):
        """ Package selection handler """
        path = self.sort_store.convert_path_to_child_path(spath)
        iterator = self.store.get_iter(path)
        obj = self.store.get_value(iterator, 0)
        self.togglePackage(obj)
        self.queueView.refresh()


class YumexQueue:
    '''
    A Queue class to store selected packages/groups and the pending actions
    '''

    def __init__(self):
        '''
        Init the queue
        '''
        self.logger = logging.getLogger('yumex.YumexQueue')
        self.packages = {}
        self._setup_packages()
        self.groups = {}
        self.groups['i'] = []
        self.groups['r'] = []
        self._name_arch_index = {}

    def _setup_packages(self):
        for key in const.QUEUE_PACKAGE_TYPES:
            self.packages[key] = []

    def clear(self):
        '''
        
        '''
        del self.packages
        self.packages = {}
        self._setup_packages()
        self.groups = {}
        self.groups['i'] = []
        self.groups['r'] = []
        self._name_arch_index = {}

    def get(self, action=None):
        '''
        
        @param action:
        '''
        if action == None:
            return self.packages
        else:
            return self.packages[action]

    def total(self):
        '''
        
        '''
        num = 0
        for key in const.QUEUE_PACKAGE_TYPES:
            num += len(self.packages[key])
        return num

    def add(self, pkg):
        '''
        
        @param pkg:
        '''
        na = "%s.%s" % (pkg.name, pkg.arch)
        if not pkg in self.packages[pkg.action] and not na in self._name_arch_index :
            self.packages[pkg.action].append(pkg)
            na = "%s.%s" % (pkg.name, pkg.arch)
            self._name_arch_index[na] = 1

    def remove(self, pkg):
        '''
        
        @param pkg:
        '''
        na = "%s.%s" % (pkg.name, pkg.arch)
        if pkg in self.packages[pkg.action]:
            self.packages[pkg.action].remove(pkg)
            del self._name_arch_index[na]

    def has_pkg_with_name_arch(self, pkg):
        na = "%s.%s" % (pkg.name, pkg.arch)
        return na in self._name_arch_index

    def addGroup(self, grp, action):
        '''
        
        @param grp:
        @param action:
        '''
        pkg_list = self.groups[action]
        if not grp in pkg_list:
            pkg_list.append(grp)
        self.groups[action] = pkg_list

    def removeGroup(self, grp, action):
        '''
        
        @param grp:
        @param action:
        '''
        pkg_list = self.groups[action]
        if grp in pkg_list:
            pkg_list.remove(grp)
        self.groups[action] = pkg_list

    def remove_all_groups(self):
        '''
        remove all groups from queue
        '''
        for action in ('i', 'r'):
            for grp in self.groups[action]:
                self.removeGroup(grp, action)


    def hasGroup(self, grp):
        '''
        
        @param grp:
        '''
        for action in ['i', 'r']:
            if grp in self.groups[action]:
                return action
        return None

    def dump(self):
        '''
        
        '''
        self.logger.info(_("Package Queue:"))
        for action in ['install', 'update', 'remove']:
            a = action[0]
            pkg_list = self.packages[a]
            if len(pkg_list) > 0:
                self.logger.info(" Package(s) to %s" % action)
                for pkg in pkg_list:
                    self.logger.info(" ---> %s " % str(pkg))
        for action in ['install', 'remove']:
            a = action[0]
            pkg_list = self.groups[a]
            if len(pkg_list) > 0:
                self.logger.info(" Group(s) to %s" % action)
                for grp in pkg_list:
                    self.logger.info(" ---> %s " % grp)


class YumexQueueView:
    """ Queue View Class"""
    def __init__(self, widget):
        '''
        
        @param widget:
        '''
        self.view = widget
        self.view.modify_font(const.SMALL_FONT)
        self.model = self.setup_view()
        self.queue = YumexQueue()

    def setup_view(self):
        """ Create Notebook list for single page  """
        model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.view.set_model(model)
        cell1 = gtk.CellRendererText()
        column1 = gtk.TreeViewColumn(_("Packages"), cell1, markup=0)
        column1.set_resizable(True)
        self.view.append_column(column1)

        cell2 = gtk.CellRendererText()
        column2 = gtk.TreeViewColumn(_("Summary"), cell2, text=1)
        column2.set_resizable(True)
        self.view.append_column(column2)
        model.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        return model

    def deleteSelected(self):
        '''
        
        '''
        rmvlist = []
        model, paths = self.view.get_selection().get_selected_rows()
        for path in paths:
            row = model[path]
            if row.parent != None:
                rmvlist.append(row[0])
        for pkg in self.getPkgsFromList(rmvlist):
            pkg.queued = None
            pkg.set_select(not pkg.selected)
        for action in const.QUEUE_PACKAGE_TYPES:
            pkg_list = self.queue.get(action)
            if pkg_list:
                self.queue.packages[action] = [x for x in pkg_list if str(x) not in rmvlist]
        self.refresh()


    def getPkgsFromList(self, rlist):
        '''
        
        @param rlist:
        '''
        rclist = []
        for action in const.QUEUE_PACKAGE_TYPES:
            pkg_list = self.queue.packages[action]
            if pkg_list:
                rclist.extend([x for x in pkg_list if str(x) in rlist])
        return rclist

    def refresh (self):
        """ Populate view with data from queue """
        self.model.clear()
        pkg_list = self.queue.packages['u'] + self.queue.packages['o']
        label = "<b>%s</b>" % P_("Package to update", "Packages to update", len(pkg_list))
        if len(pkg_list) > 0:
            self.populate_list(label, pkg_list)
        pkg_list = self.queue.packages['i']
        label = "<b>%s</b>" % P_("Package to install", "Packages to install", len(pkg_list))
        if len(pkg_list) > 0:
            self.populate_list(label, pkg_list)
        pkg_list = self.queue.packages['r']
        label = "<b>%s</b>" % P_("Package to remove", "Packages to remove", len(pkg_list))
        if len(pkg_list) > 0:
            self.populate_list(label, pkg_list)
        pkg_list = self.queue.packages['ri']
        label = "<b>%s</b>" % P_("Package to reinstall", "Packages to reinstall", len(pkg_list))
        if len(pkg_list) > 0:
            self.populate_list(label, pkg_list)
        pkg_list = self.queue.packages['li']
        label = "<b>%s</b>" % P_("RPM file to install", "RPM files to install", len(pkg_list))
        if len(pkg_list) > 0:
            self.populate_list(label, pkg_list)
        self.populate_list_downgrade()
        self.view.expand_all()

    def populate_list(self, label, pkg_list):
        '''
        
        @param label:
        @param pkg_list:
        '''
        parent = self.model.append(None, [label, ""])
        for pkg in pkg_list:
            self.model.append(parent, [str(pkg), pkg.summary])

    def populate_list_downgrade(self):
        '''
        
        '''
        pkg_list = self.queue.packages['do']
        label = "<b>%s</b>" % P_("Package to downgrade", "Packages to downgrade", len(pkg_list))
        if len(pkg_list) > 0:
            parent = self.model.append(None, [label, ""])
            for pkg in pkg_list:
                item = self.model.append(parent, [str(pkg), pkg.summary])
                self.model.append(item, [_("<b>Downgrade to</b> %s ") % str(pkg.downgrade_po), ""])

class YumexRepoView(SelectionView):
    """ 
    This class controls the repo TreeView
    """
    def __init__(self, widget):
        '''
        
        @param widget:
        '''
        SelectionView.__init__(self, widget)
        self.view.modify_font(const.SMALL_FONT)
        self.headers = [_('Repository'), _('Filename')]
        self.store = self.setup_view()
        self.state = 'normal'
        self._last_selected = []

    def on_toggled(self, widget, path):
        """ Repo select/unselect handler """
        iterator = self.store.get_iter(path)
        state = self.store.get_value(iterator, 0)
        self.store.set_value(iterator, 0, not state)

    def on_section_header_clicked(self, widget):
        """  Selection column header clicked"""
        if self.state == 'normal': # deselect all
            self._last_selected = self.get_selected()
            self.deselect_all()
            self.state = 'deselected'
        elif self.state == 'deselected': # select all
            self.state = 'selected'
            self.select_all()
        elif self.state == 'selected': # select previous selected
            self.state = 'normal'
            self.select_by_keys(self._last_selected)
            self._last_selected = []


    def setup_view(self):
        """ Create models and columns for the Repo TextView  """
        store = gtk.ListStore('gboolean', gobject.TYPE_STRING, gobject.TYPE_STRING, 'gboolean')
        self.view.set_model(store)
        # Setup Selection Column
        col = self.create_selection_column_num(0)
        col.set_clickable(True)
        col.connect('clicked', self.on_section_header_clicked)

        # Setup resent column
        cell2 = gtk.CellRendererPixbuf()    # gpgcheck
        cell2.set_property('stock-id', gtk.STOCK_DIALOG_AUTHENTICATION)
        column2 = gtk.TreeViewColumn("", cell2)
        column2.set_cell_data_func(cell2, self.new_pixbuf)
        column2.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column2.set_fixed_width(20)
        column2.set_sort_column_id(-1)
        self.view.append_column(column2)

        # Setup reponame & repofile column's
        self.create_text_column_num(_('Repository'), 1)
        self.create_text_column_num(_('Name'), 2)
        self.view.set_search_column(1)
        self.view.set_reorderable(False)
        return store

    def populate(self, data, showAll=False):
        """ Populate a repo liststore with data """
        self.store.clear()
        for state, ident, name, gpg in data:
            if not self.isHidden(ident) or showAll:
                self.store.append([state, ident, name, gpg])

    def isHidden(self, ident):
        '''
        
        @param ident:
        '''
        for hide in const.REPO_HIDE:
            if hide in ident:
                return True
        else:
            return False

    def new_pixbuf(self, column, cell, model, iterator):
        '''
        
        @param column:
        @param cell:
        @param model:
        @param iterator:
        '''
        gpg = model.get_value(iterator, 3)
        if gpg:
            cell.set_property('visible', True)
        else:
            cell.set_property('visible', False)

    def get_selected(self):
        '''
        
        '''
        selected = []
        for elem in self.store:
            state = elem[0]
            name = elem[1]
            if state:
                selected.append(name)
        return selected

    def get_notselected(self):
        '''
        
        '''
        notselected = []
        for elem in self.store:
            state = elem[0]
            name = elem[1]
            if not state:
                notselected.append(name)
        return notselected

    def deselect_all(self):
        '''
        
        '''
        iterator = self.store.get_iter_first()
        while iterator != None:
            self.store.set_value(iterator, 0, False)
            iterator = self.store.iter_next(iterator)

    def select_all(self):
        '''
        
        '''
        iterator = self.store.get_iter_first()
        while iterator != None:
            self.store.set_value(iterator, 0, True)
            iterator = self.store.iter_next(iterator)


    def select_by_keys(self, keys):
        '''
        
        @param keys:
        '''
        iterator = self.store.get_iter_first()
        while iterator != None:
            repoid = self.store.get_value(iterator, 1)
            if repoid in keys:
                self.store.set_value(iterator, 0, True)
            else:
                self.store.set_value(iterator, 0, False)
            iterator = self.store.iter_next(iterator)

class YumexSearchOptionsView(SelectionView):
    """ 
    This class controls the search option TreeView
    """
    def __init__(self, widget):
        '''
        
        @param widget:
        '''
        SelectionView.__init__(self, widget)
        self.view.modify_font(const.SMALL_FONT)
        self.store = self.setup_view()

    def on_toggled(self, widget, path):
        """ Repo select/unselect handler """
        iterator = self.store.get_iter(path)
        state = self.store.get_value(iterator, 0)
        self.store.set_value(iterator, 0, not state)


    def get_selected(self):
        '''
        
        '''
        selected = []
        for elem in self.store:
            state = elem[0]
            name = elem[2]
            if state:
                selected.append(name)
        return selected

    def setup_view(self):
        """ Create models and columns for the Search Options TextView  """
        store = gtk.ListStore('gboolean', gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.view.set_model(store)
        # Setup Selection Column
        col = self.create_selection_column_num(0)
        # Setup reponame & repofile column's
        self.create_text_column_num(_('Search Keys'), 1)
        return store

    def populate(self, values, default_values):
        self.store.clear()
        for key in const.SEARCH_KEYS_ORDER:
            if key in default_values:
                state = True
            else:
                state = False
            self.store.append([state, values[key], key])


class YumexGroupView:
    '''
    '''

    def __init__(self, treeview, qview, base):
        '''
        
        @param treeview:
        @param qview:
        @param base:
        '''
        self.view = treeview
        self.base = base
        self.view.modify_font(const.SMALL_FONT)
        self.model = self.setup_view()
        self.queue = qview.queue
        self.queueView = qview
        self.yumbase = None # it will se set later 
        self.currentCategory = None
        self.icon_theme = gtk.icon_theme_get_default()
        self._groups = None


    def setup_view(self):
        """ Setup Group View  """
        model = gtk.TreeStore(gobject.TYPE_BOOLEAN, # 0 Installed
                              gobject.TYPE_STRING, # 1 Group Name
                              gobject.TYPE_STRING, # 2 Group Id
                              gobject.TYPE_BOOLEAN, # 3 In queue          
                              gobject.TYPE_BOOLEAN, # 4 isCategory   
                              gobject.TYPE_STRING)  # 5 Description     


        self.view.set_model(model)
        column = gtk.TreeViewColumn(None, None)
        # Selection checkbox
        selection = gtk.CellRendererToggle()    # Selection
        selection.set_property('activatable', True)
        column.pack_start(selection, False)
        column.set_cell_data_func(selection, self.setCheckbox)
        selection.connect("toggled", self.on_toggled)
        self.view.append_column(column)

        column = gtk.TreeViewColumn(None, None)
        # Queue Status (install/remove group)
        state = gtk.CellRendererPixbuf()    # Queue Status
        state.set_property('stock-size', 1)
        column.pack_start(state, False)
        column.set_cell_data_func(state, self.queue_pixbuf)

        # category/group icons 
        icon = gtk.CellRendererPixbuf()
        icon.set_property('stock-size', 1)
        column.pack_start(icon, False)
        column.set_cell_data_func(icon, self.grp_pixbuf)

        category = gtk.CellRendererText()
        column.pack_start(category, False)
        column.add_attribute(category, 'markup', 1)

        self.view.append_column(column)
        self.view.set_headers_visible(False)
        return model

    def setCheckbox(self, column, cell, model, iterator):
        '''
        
        @param column:
        @param cell:
        @param model:
        @param iterator:
        '''
        isCategory = model.get_value(iterator, 4)
        state = model.get_value(iterator, 0)
        if isCategory:
            cell.set_property('visible', False)
        else:
            cell.set_property('visible', True)
            cell.set_property('active', state)

    def on_toggled(self, widget, path):
        """ Group selection handler """
        iterator = self.model.get_iter(path)
        grpid = self.model.get_value(iterator, 2)
        inst = self.model.get_value(iterator, 0)
        action = self.queue.hasGroup(grpid)
        if action: # Group is in the queue, remove it from the queue
            self.queue.removeGroup(grpid, action)
            self._updatePackages(grpid, False, None)
            self.model.set_value(iterator, 3, False)
        else:
            if inst: # Group is installed add it to queue for removal
                self.queue.addGroup(grpid, 'r') # Add for remove           
                self._updatePackages(grpid, True, 'r')
            else: # Group is not installed, add it to queue for installation
                self.queue.addGroup(grpid, 'i') # Add for install
                self._updatePackages(grpid, True, 'i')
            self.model.set_value(iterator, 3, True)
        self.model.set_value(iterator, 0, not inst)


    def _updatePackages(self, grpid, add, action):
        '''
        
        @param grpid:
        @param add:
        @param action:
        '''
        pkgs = self.base.backend.get_group_packages(grpid, 'default')
        # Add group packages to queue
        if add:
            for po in pkgs:
                if not po.queued:
                    if action == 'i' and not po.is_installed() : # Install
                        po.queued = po.action
                        self.queue.add(po)
                        po.set_select(True)
                    elif action == 'r' and po.is_installed() : # Remove
                        po.queued = po.action
                        self.queue.add(po)
                        po.set_select(False)
        # Remove group packages from queue
        else:
            for po in pkgs:
                if po.queued:
                    po.queued = None
                    self.queue.remove(po)
                    po.set_select(not po.selected)
        self.queueView.refresh()

    def reset_queued(self):
        '''
        Reset the selection of all queued groups
        used to undo the selection
        '''
        for row in self.model: # Loop trough the categories
            children = row.iterchildren() # get the children
            if children: # is there any children
                for elem in children: # loop trough the groups
                    if elem[3] == True: # if in queue
                        elem[3] = False
                        elem[0] = not elem[0] # invert the section

    def populate(self, data):
        '''
        
        @param data:
        '''
        self.model.clear()
        self._groups = data
        for cat, catgrps in data:
            (catid, name, desc) = cat
            node = self.model.append(None, [None, name, catid, False, True, desc])
            for grp in catgrps:
                (grpid, grp_name, grp_desc, inst, icon) = grp
                self.model.append(node, [inst, grp_name, grpid, False, False, grp_desc])


    def queue_pixbuf(self, column, cell, model, iterator):
        """ 
        Cell Data function for recent Column, shows pixmap
        if recent Value is True.
        """
        grpid = model.get_value(iterator, 2)
        queued = model.get_value(iterator, 3)
        action = self.queue.hasGroup(grpid)
        if action:
            if action == 'i':
                icon = 'network-server'
            else:
                icon = 'edit-delete'
            cell.set_property('visible', True)
            cell.set_property('icon-name', icon)
        cell.set_property('visible', queued)

    def grp_pixbuf(self, column, cell, model, iterator):
        """ 
        Cell Data function for recent Column, shows pixmap
        if recent Value is True.
        """
        grpid = model.get_value(iterator, 2)
        pix = None
        fn = "/usr/share/pixmaps/comps/%s.png" % grpid
        if os.access(fn, os.R_OK):
            pix = self._get_pix(fn)
        if pix:
            cell.set_property('visible', True)
            cell.set_property('pixbuf', pix)
        else:
            cell.set_property('visible', False)


    def _get_pix(self, fn):
        '''
        
        @param fn:
        '''
        imgsize = 24
        pix = gtk.gdk.pixbuf_new_from_file(fn)
        if pix.get_height() != imgsize or pix.get_width() != imgsize:
            pix = pix.scale_simple(imgsize, imgsize,
                                   gtk.gdk.INTERP_BILINEAR)
        return pix

class YumexCategoryTypesView(SelectionView):
    '''
    '''

    def __init__(self, widget):
        SelectionView.__init__(self, widget)
        self.model = self.setup_view()
        self.view.modify_font(const.SMALL_FONT)

    def setup_view(self):
        """ Create models and columns for the TextView  """

        store = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.view.set_model(store)
        self.create_text_column_num(_('Categories'), 1)
        return store

    def populate(self, data):
        self.model.clear()
        for (id, txt) in data:
            self.model.append([id, txt])


class YumexCategoryContentView(SelectionView):
    '''
    '''

    def __init__(self, widget):
        SelectionView.__init__(self, widget)
        self.model = self.setup_view()
        self.view.modify_font(const.SMALL_FONT)

    def setup_view(self):
        """ Create models and columns for the TextView  """
        store = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.view.set_model(store)
        self.create_text_column_num('', 1)
        self.view.set_headers_visible(False)
        return store

    def populate(self, data):
        self.model.clear()
        for (id, txt) in data:
            self.model.append([id, txt])


class YumexHistoryView(SelectionView):
    '''
    '''

    def __init__(self, widget):
        SelectionView.__init__(self, widget)
        self.model = self.setup_view()
        self.view.modify_font(const.SMALL_FONT)

    def setup_view(self):
        """ Create models and columns for the TextView  """
        store = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, \
                              gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.view.set_model(store)
        self.create_text_column_num(_('Id'), 0)
        self.create_text_column_num(_('Login User'), 1)
        self.create_text_column_num(_('Data/Time'), 2)
        self.create_text_column_num(_('Action(s)'), 3)
        self.create_text_column_num(_('Altered'), 4)
        return store

    def populate(self, data):
        self.model.clear()
        for (id, user, dt, action, alt) in data:
            self.model.append([str(id), user, dt, action, str(alt)])

class HistoryLabel:
    """
    Fake History Package class contain a category label
    """
    def __init__(self, label):
        self.name = "<b>%s</b>" % label
        self.installed = False
        self.fullver = ""
        self.arch = ""


class YumexHistoryPackageView(SelectionView):
    """ 
    This class controls the history package
    """
    def __init__(self, widget, install_color, other_color):
        '''
        
        @param widget:
        '''
        SelectionView.__init__(self, widget)
        self.view.modify_font(const.SMALL_FONT)
        self.store = self.setup_view()
        self.install_color = install_color
        self.other_color = other_color

    def get_data_bool(self, column, cell, model, iterator, prop):
        '''
        Show a checkbox is selection column is not None
        
        @param column:
        @param cell:
        @param model:
        @param iterator:
        '''
        state = model.get_value(iterator, 0)
        category = model.get_value(iterator, 1)
        if category:
            cell.set_property('visible', False)
        else:
            cell.set_property('visible', True)
            cell.set_property('active', state)

    def get_data_text(self, column, cell, model, iterator, prop):
        '''
        a property function to get string data from a object in the TreeStore based on
        an attributes key
        @param column:
        @param cell:
        @param model:
        @param iterator:
        @param prop: attribute key
        '''
        category = model.get_value(iterator, 1)
        color = self.other_color
        if category:
            if prop == 'name':
                cell.set_property('markup', category)
            else:
                cell.set_property('markup', '')
        else:
            obj = model.get_value(iterator, 2)
            if obj:
                cell.set_property('markup', getattr(obj, prop))
                if obj.installed:
                    color = self.install_color
        cell.set_property('foreground', color)


    def on_toggled(self, widget, path):
        """ Repo select/unselect handler """
        iterator = self.store.get_iter(path)
        state = self.store.get_value(iterator, 0)
        self.store.set_value(iterator, 0, not state)


    def get_selected(self):
        '''
        
        '''
        selected = []
        for elem in self.store:
            state = elem[0]
            name = elem[1]
            if state:
                selected.append(name)
        return selected

    def setup_view(self):
        """ Create models and columns for the Search Options TextView  """
        store = gtk.TreeStore('gboolean', gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
        self.view.set_model(store)
        # Setup Selection Column
        #self.create_selection_colunm('')
        # Setup Actions and pacakges
        col = self.create_text_column(_("Package"), 'name', size=250)
        self.view.set_expander_column(col)
        self.create_text_column(_("Ver."), 'fullver', size=120)
        self.create_text_column(_("Arch."), 'arch' , size=60)
        return store

    def _add_values(self, cat, elements):
        main_label = "<b>%s</b>" % cat
        parent = self.store.append(None, [False, main_label, HistoryLabel(cat)])
        # history packages
        for elem in elements:
            if isinstance(elem, tuple):
                new = self.store.append(parent, [False, "", elem[1]])
                self.store.append(new, [False, "", elem[0]])
            else:
                self.store.append(parent, [False, "", elem])

    def populate(self, main, secondary):
        self.store.clear()
        # Main Categories
        for state in const.HISTORY_SORT_ORDER:
            if state in main:
                elements = main[state]
                cat = const.HISTORY_STATE_LABLES[state]
                self._add_values(cat, elements)
        for cat in secondary:
            elements = secondary[cat]
            self._add_values(cat, elements)

class YumexDepsPackageView(SelectionView):
    """ 
    This class controls the history package
    """
    def __init__(self, widget, install_color, other_color):
        '''
        
        @param widget:
        '''
        SelectionView.__init__(self, widget)
        self.view.modify_font(const.SMALL_FONT)
        self.store = self.setup_view()
        self.install_color = install_color
        self.other_color = other_color

    def get_data_bool(self, column, cell, model, iterator, prop):
        '''
        Show a checkbox is selection column is not None
        
        @param column:
        @param cell:
        @param model:
        @param iterator:
        '''
        state = model.get_value(iterator, 0)
        category = model.get_value(iterator, 1)
        if category:
            cell.set_property('visible', False)
        else:
            cell.set_property('visible', True)
            cell.set_property('active', state)

    def get_data_text(self, column, cell, model, iterator, prop):
        '''
        a property function to get string data from a object in the TreeStore based on
        an attributes key
        @param column:
        @param cell:
        @param model:
        @param iterator:
        @param prop: attribute key
        '''
        category = model.get_value(iterator, 1)
        color = self.other_color
        if category:
            if prop == 'name':
                cell.set_property('markup', category)
            else:
                cell.set_property('markup', '')
        else:
            obj = model.get_value(iterator, 2)
            if obj:
                cell.set_property('markup', getattr(obj, prop))
                if obj.installed:
                    color = self.install_color
        cell.set_property('foreground', color)


    def on_toggled(self, widget, path):
        """ Repo select/unselect handler """
        iterator = self.store.get_iter(path)
        state = self.store.get_value(iterator, 0)
        self.store.set_value(iterator, 0, not state)


    def get_selected(self):
        '''
        
        '''
        selected = []
        for elem in self.store:
            state = elem[0]
            name = elem[1]
            if state:
                selected.append(name)
        return selected

    def setup_view(self):
        """ Create models and columns for the Search Options TextView  """
        store = gtk.TreeStore('gboolean', gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
        self.view.set_model(store)
        # Setup Selection Column
        #self.create_selection_colunm('')
        # Setup Actions and pacakges
        col = self.create_text_column(_("Package"), 'name', size=350)
        self.view.set_expander_column(col)
        self.create_text_column(_("Ver."), 'fullver', size=120)
        self.create_text_column(_("Arch."), 'arch' , size=60)
        return store


    def populate(self, deps):
        self.store.clear()
        for req in sorted(deps):
            parent = self.store.append(None, [False, "<b>%s</b>" % str(req), None])
            for provider in deps[req]:
                self.store.append(parent, [False, "", provider])











