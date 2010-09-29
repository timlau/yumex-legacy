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

# Yumex gui classes & functions

'''
'''

import gtk

import gconf, subprocess

from datetime import date
from yumexbase.constants import *
from yumexbackend.yum_backend import YumexPackageYum
from guihelpers import TextViewBase, busyCursor, normalCursor
from yum.i18n import utf8_text_wrap


# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
import logging
from yumexbase.i18n import _, P_
# pylint: enable-msg=W0611

#
# Classses
#

class PackageInfoTextView(TextViewBase):
    '''
    TextView handler for showing package information
    '''
    
    def __init__(self, textview, font_size=8, window=None, url_handler=None):
        '''
        Setup the textview
        @param textview: the gtk.TextView widget to use 
        @param font_size: default text size
        '''
        TextViewBase.__init__(self, textview, window, url_handler)        

        # description style
        tag = "description"
        style = gtk.TextTag(tag)
        style.set_property("foreground", "midnight blue")
        style.set_property("family", "Monospace")
        style.set_property("size_points", font_size)
        self.add_style(tag, style)
        self.default_style = tag

        # filelist style
        tag = "filelist"
        style = gtk.TextTag(tag)
        style.set_property("foreground", "DarkOrchid4")
        style.set_property("family", "Monospace")
        style.set_property("size_points", font_size)
        self.add_style(tag, style)

        # changelog style
        tag = "changelog"
        style = gtk.TextTag(tag)
        style.set_property("foreground", "midnight blue")
        style.set_property("family", "Monospace")
        style.set_property("size_points", font_size)
        self.add_style(tag, style)
        
        # changelog style
        tag = "changelog-header"
        style = gtk.TextTag(tag)
        style.set_property("foreground", "dark red")
        style.set_property("family", "Monospace")
        style.set_property("size_points", font_size)
        self.add_style(tag, style)
        

class PageHeader(gtk.HBox):
    ''' Page header to show in top of Notebook Page'''
    
    def __init__(self, text, icon=None):
        ''' 
        setup the notebook page header
        @param text: Page Title
        @param icon: icon filename
        '''
        gtk.HBox.__init__(self)
        # Setup Label
        self.label = gtk.Label()
        markup = '<span foreground="blue" size="x-large">%s</span>' % text
        self.label.set_markup(markup)
        self.label.set_padding(10, 0)
        # Setup Icon
        self.icon = gtk.Image()
        if icon:
            self.icon.set_from_file(icon)
        else:
            self.icon.set_from_icon_name('gtk-dialog-info', 6)
        self.pack_start(self.label, expand=False)
        self.pack_end(self.icon, expand=False)
        self.show_all()

class SelectorBase:
    ''' Button selector base '''
    
    def __init__(self, content, key_bindings=None):
        '''
        Setup the selector
        @param content: a gtk.VBox widget to contain the selector buttons
        '''
        self.content = content
        self._buttons = {}
        self._first = None
        self._selected = None
        self.key_bindings = key_bindings
        
    def add_button(self, key, icon=None, stock=None, tooltip=None, accel=None):
        ''' Add a new selector button '''
        if len(self._buttons) == 0:
            button = gtk.RadioButton(None)
            self._first = button
        else:
            button = gtk.RadioButton(self._first)
        button.connect("clicked", self.on_button_clicked, key)
        if accel:
            keyval,mask = gtk.accelerator_parse(accel)
            button.add_accelerator("clicked", self.key_bindings, keyval, mask, 0)
    
        button.set_relief(gtk.RELIEF_NONE)
        button.set_mode(False)
        if stock:
            pix = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU)
        else: 
            pb = gtk.gdk.pixbuf_new_from_file(icon)            
            pix = gtk.Image()
            pix.set_from_pixbuf(pb)
        pix.show()
        button.add(pix)
    
        if tooltip:
            button.set_tooltip_text(tooltip)
        button.show()
        self.content.pack_start(button, False)
        self._buttons[key] = button

    def set_active(self, key):
        ''' set the active selector button '''
        if key in self._buttons:
            button = self._buttons[key]
            button.clicked()
            
    def get_active(self):
        ''' get the active selector button'''
        return self._selected            
            
    def on_button_clicked(self, widget=None, key=None):
        ''' button clicked callback handler'''
        if widget.get_active(): # only work on the active button
            self._selected = key
            
    def hide_button(self, key):
        if key in self._buttons:
            button = self._buttons[key]
            button.hide()

    def show_button(self, key):
        if key in self._buttons:
            button = self._buttons[key]
            button.show()

class PackageInfo(SelectorBase):
    '''
    Package information gui handler
    controls the package info Textview and the buttons to show
    description, changelog and filelist.
    '''
    
    def __init__(self, main, console, selector, frontend, font_size=8):
        '''
        Setup the package info
        @param main: main window
        @param console: Widget for writing infomation (gtk.TextView)
        @param selector: the selector ui widget (gtk.VBox)
        @param frontend: the frontend instance
        @param font_size: the fontsize in the console
        '''
        SelectorBase.__init__(self, selector, key_bindings = frontend.key_bindings)
        self.widget = console
        self.console = PackageInfoTextView(console, font_size=font_size, window=main, url_handler = self._url_handler )
        self.main_window = main
        self.frontend = frontend
        self.add_button('description', stock='gtk-about', 
                        tooltip=_('Package Description'), accel = '<Shift>d')
        self.add_button('update', stock='gtk-info', 
                        tooltip=_('Update information'), accel = '<Shift>u')
        self.add_button('changelog', stock='gtk-edit', 
                        tooltip=_('Package Changelog'), accel = '<Shift>c')
        self.add_button('filelist', stock='gtk-harddisk', 
                        tooltip=_('Package Filelist'), accel = '<Shift>f')
        self.pkg = None
        self._selected = 'description'

    def _url_handler(self, url):
        self.frontend.info('Url activated : ' + url)
        client = gconf.client_get_default()
        browser = client.get_string("/desktop/gnome/url-handlers/http/command") or "firefox %s"
        # Because URLs contain & it needs to be quoted
        browser = browser % '"' + url + '"'
        subprocess.Popen(args=browser, shell=True)
        
    def update(self, pkg):
        '''
        update the package info with a new package
        @param pkg: package to show info for
        @param update: package is an update (used to display update info) 
        '''
        self.widget.grab_add() # lock everything but then TextView widget, until we have updated
        self.pkg = pkg
        #self.set_active(self._selected)
        key = self._selected
        self.update_console(key)
        self.widget.grab_remove()
        
    def clear(self):        
        '''
        clear the package info console
        '''
        
        
        self.console.clear()

    def on_button_clicked(self, widget=None, key=None):
        ''' button clicked callback handler'''
        if widget.get_active(): # only work on the active button
            self._selected = key
            self.update_console(key)
    
    def update_console(self, key):
        '''
        update the console with information
        @param key: information to show (description,changelog,filelist)
        '''
        if self.pkg:
            busyCursor(self.main_window)
            self.console.clear()
            if key == 'description':
                self.show_description()
            elif key == 'changelog':
                self.show_changelog()
            elif key == 'filelist':
                self.show_filelist()
            elif key == 'update':
                self.show_update()
            self.console.goTop()
            normalCursor(self.main_window)

    def show_update(self):
        '''
        show the package description
        '''
        upd_info = None
        updated_po = None
        upd_info_list, updated_po_list = self.pkg.updateinfo
        progress = self.frontend.get_progress()
        progress.hide()
        if not upd_info_list:
            return
        for i in xrange(0,len(upd_info_list)):
            ndx = (len(upd_info_list)-1) - i 
            upd_info = upd_info_list[ndx]
            updated_po = updated_po_list[ndx]
            if updated_po and updated_po <> 'None':
                msg = "%s (%s) --> %s \n\n" % (self.pkg.fullname, self.pkg.size,  updated_po)                
                self.console.write(msg,"changelog-header")   
            if upd_info:
                msg = "%s\n\n" % upd_info['update_id'] 
                self.console.write(msg,"changelog-header")   
                self.show_update_info(upd_info)
        
    def show_description(self):
        '''
        show the package description
        '''
        url = self.pkg.URL
        self.console.write(_("Project URL : "), "changelog-header", newline = False)
        self.console.add_url(url,url, newline = True)
        self.console.write('\n')
        self.console.write(self.pkg.description)

    def show_update_info(self,upd_info):
        head = ""
        head += ("%14s " % _("Release"))   + ": %(release)s\n" 
        head += ("%14s " % _("Type"))      + ": %(type)s\n"
        head += ("%14s " % _("Status"))    + ": %(status)s\n"
        head += ("%14s " % _("Issued"))    + ": %(issued)s\n"
        head = head  % upd_info

        if upd_info['updated'] and upd_info['updated'] != upd_info['issued']:
            head += "    Updated : %s" % upd_info['updated']

        self.console.write(head)
        head = ""

        # Add our bugzilla references
        if upd_info['references']:
            bzs = [ r for r in upd_info['references'] if r and r['type'] == 'bugzilla']
            if len(bzs):
                header = "Bugzilla"
                buglist =""
                for bz in bzs:
                    if 'title' in bz and bz['title']:
                        bug_msg = ' - %s' % bz['title']
                    else:
                        bug_msg = ''
                    self.console.write("%14s : " % header, newline = False)   
                    self.console.add_url(bz['id'],self.frontend.settings.bugzilla_url+bz['id']) 
                    self.console.write(bug_msg)
                    header = " "

        # Add our CVE references
        if upd_info['references']:
            cves = [ r for r in upd_info['references'] if r and r['type'] == 'cve']
            if len(cves):
                cvelist = ""
                header = "CVE"
                for cve in cves:
                    cvelist += "%14s : %s\n" % (header, cve['id'])
                    header = " "
                head += cvelist[: - 1].rstrip() + '\n\n'

        if upd_info['description'] is not None:
            desc = utf8_text_wrap(upd_info['description'], width=64,
                                  subsequent_indent=' ' * 14 + ' : ')
            head += "%14s : %s\n" % (_("Description"), '\n'.join(desc))
            
        head += "\n"
        self.console.write(head)
        
    def show_changelog(self):
        '''
        show the package changelog 
        '''
        changelog = self.pkg.changelog
        progress = self.frontend.get_progress()
        progress.hide()        
        if changelog:
            for (c_date, c_ver, msg) in changelog:
                self.console.write("* %s %s" % (date.fromtimestamp(c_date).isoformat(), c_ver), "changelog-header")
                for line in msg.split('\n'):
                    self.console.write("%s" % line, "changelog")
                self.console.write('\n')              

    def show_filelist(self):
        '''
        show the package filelist
        '''
        files = self.pkg.filelist
        progress = self.frontend.get_progress()
        progress.hide()     
        if files: # files can be None   
            files.sort()
            for fn in files:
                self.console.write(fn, "filelist")
        
        
        
        
        
        
class PageSelector(SelectorBase):
    ''' Button notebook selector '''
    
    def __init__(self, content, notebook, key_bindings=None):
        ''' setup the selector '''
        SelectorBase.__init__(self, content, key_bindings)
        self.notebook = notebook
    def on_button_clicked(self, widget=None, key=None):
        ''' button clicked callback handler'''
        if widget.get_active(): # only work on the active button
            self.notebook.set_page(key) # set the new notebook page
            self._selected = key
            
class Notebook:
    ''' Notebook with button selector '''
    
    def __init__(self, notebook, selector, key_bindings=None):
        ''' setup the notebook and the selector '''
        self.notebook = notebook
        self.selector = PageSelector(selector, self, key_bindings)
        self._pages = {}
        self._callbacks = {}

    def add_page(self, key, title, widget, icon=None, tooltip=None, header=True, accel=None, callback=None ):
        ''' 
        Add a new page and selector button to notebook
        @param key: the page key (name) used by reference the page
        @param widget: the widget container to insert into the page
        @param icon: an optional icon file for the selector button
        @param tooltip: an optional tooltip for the selector button  
        '''
        num = len(self._pages)
        container = gtk.VBox()
        self._pages[key] = (num, container)
        if header:
            header = PageHeader(title, icon)
            container.pack_start(header, expand=False, padding=5)
            sep = gtk.HSeparator()
            sep.show()
            container.pack_start(sep, expand=False)
        # get the content from the widget and reparent it and add it to page    
        content = gtk.VBox()
        widget.reparent(content)
        container.pack_start(content, expand=True)
        content.show()
        container.show()
        self.notebook.append_page(container)
        # Add selector button
        self.selector.add_button(key, icon=icon, tooltip=tooltip, accel=accel)
        if callback:
            self._callbacks[key] = callback
        
    def set_active(self, key):
        '''
        set the active page in notebook and selector
        @param key: the page key (name) used by reference the page
        '''
        self.selector.set_active(key)
        
    def set_page(self, key):
        '''
        set the current notebook page
        '''
        if key in self._pages:
            num, widget = self._pages[key]
            self.notebook.set_current_page(num)
            if key in self._callbacks:
                callback = self._callbacks[key]
                callback()

                    