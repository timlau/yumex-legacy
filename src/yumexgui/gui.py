#!/usr/bin/python -tt
# -*- coding: iso-8859-1 -*-
#    Yum Exteder (yumex) - A GUI for yum
#    Copyright (C) 2008 Tim Lauridsen < tim<AT>yum-extender<DOT>org >
#    modified 2013 by Beat Kueng <beat-kueng@gmx.net>
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
import cairo
import random


from datetime import date
from yumexbase.constants import *
from guihelpers import TextViewBase, busyCursor, normalCursor
from yum.i18n import utf8_text_wrap
from yumexgui.views import YumexDepsPackageView
from subprocess import call
import re
from operator import itemgetter, attrgetter

# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
from yumexbase import _, P_  # lint:ok
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
            keyval, mask = gtk.accelerator_parse(accel)
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
        SelectorBase.__init__(self, selector, key_bindings=frontend.key_bindings)
        self.widget = console
        self.main_window = main
        self.frontend = frontend
        self.console = PackageInfoTextView(console, font_size=font_size, window=main, \
                                            url_handler=self._url_handler)
        self.deps_view = YumexDepsPackageView(self.frontend.ui.packageDeps, \
                                              self.frontend.settings.color_install, \
                                              self.frontend.settings.color_normal)
        self.add_button('description', stock='gtk-about',
                        tooltip=_('Package Description'), accel='<alt>i')
        self.add_button('update', stock='gtk-info',
                        tooltip=_('Update information'), accel='<alt>u')
        self.add_button('changelog', stock='gtk-edit',
                        tooltip=_('Package Changelog'), accel='<alt>c')
        self.add_button('filelist', stock='gtk-harddisk',
                        tooltip=_('Package Filelist'), accel='<alt>f')
        self.add_button('deps', stock='gtk-convert',
                        tooltip=_('Package Dependencies'), accel='<alt>d')
        self.pkg = None
        self._selected = 'description'
        self._set_output_view('description')

    def _is_url(self,url):
        urls = re.findall('^http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+~]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url)
        if urls:
            return True
        else:
            return False

    def _url_handler(self, url):
        self.frontend.info('Url activated : ' + url)
        if self._is_url(url): # just to be sure and prevent shell injection
            rc = call("xdg-open %s"%url, shell=True)
            if rc != 0: # failover to gtk.show_uri, if xdg-open fails or is not installed
                gtk.show_uri(None, url, gtk.gdk.CURRENT_TIME)
        else:
            self.frontend.warning("%s is not an url" % url)

    def update(self, pkg):
        '''
        update the package info with a new package
        @param pkg: package to show info for
        @param update: package is an update (used to display update info)
        '''
        if pkg == self.pkg:
            return
        self.widget.grab_add() # lock everything but then TextView widget, until we have updated
        self.pkg = pkg
        #self.show_dependencies()
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

    def _set_output_view(self, key):
        if key == 'deps':
            self.frontend.ui.packageInfoSW.hide()
            self.frontend.ui.packageDepsSW.show()
        else:
            self.frontend.ui.packageInfoSW.show()
            self.frontend.ui.packageDepsSW.hide()

    def update_console(self, key):
        '''
        update the console with information
        @param key: information to show (description,changelog,filelist)
        '''
        if self.pkg:
            busyCursor(self.main_window)
            self.console.clear()
            self._set_output_view(key)
            if key == 'description':
                self.show_description()
            elif key == 'changelog':
                self.show_changelog()
            elif key == 'filelist':
                self.show_filelist()
            elif key == 'update':
                self.show_update()
            elif key == 'deps':
                self.show_dependencies()
            self.console.goTop()
            normalCursor(self.main_window)

    def show_update(self):
        '''
        show the package description
        '''
        upd_info = None
        upd_info_list, updated_po_list = self.pkg.updateinfo
        progress = self.frontend.get_progress()
        progress.hide()
        if not updated_po_list:
            self.console.write(_("No Update information"), "changelog-header", newline=False)
            return
        updated_pkgs = updated_po_list[0]
        if not upd_info_list:
            return
        if updated_pkgs:
            new_pkg = "%s (%s) --> " % (self.pkg.fullname, self.pkg.size)
            self.console.write(new_pkg, "changelog-header", newline=False)
            spaces = " " * len(new_pkg)
            i = 0
            for po in updated_pkgs:
                if i == 0:
                    msg = str(po)
                else:
                    msg = "%s %s" % (spaces,po)
                self.console.write(msg, "changelog-header")
        self.console.write('\n')
        for upd_info in sorted(upd_info_list, key=itemgetter('update_id'), reverse=True):
            if upd_info:
                msg = "%s\n\n" % upd_info['update_id']
                self.console.write(msg, "changelog-header")
                self.show_update_info(upd_info)

    def show_dependencies(self):
        deps = self.pkg.dependencies
        self.deps_view.populate(deps)

    def show_description(self):
        '''
        show the package description
        '''
        url = self.pkg.URL
        self.console.write(_("Project URL : "), "changelog-header", newline=False)
        self.console.add_url(url, url, newline=True)
        self.console.write('\n')
        self.console.write(self.pkg.description)

    def show_update_info(self, upd_info):
        head = ""
        head += ("%14s " % _("Release")) + ": %(release)s\n"
        head += ("%14s " % _("Type")) + ": %(type)s\n"
        head += ("%14s " % _("Status")) + ": %(status)s\n"
        head += ("%14s " % _("Issued")) + ": %(issued)s\n"
        head = head % upd_info

        if upd_info['updated'] and upd_info['updated'] != upd_info['issued']:
            head += "    Updated : %s" % upd_info['updated']

        self.console.write(head)
        head = ""

        # Add our bugzilla references
        if upd_info['references']:
            bzs = [ r for r in upd_info['references'] if r and r['type'] == 'bugzilla']
            if len(bzs):
                header = "Bugzilla"
                for bz in bzs:
                    if 'title' in bz and bz['title']:
                        bug_msg = ' - %s' % bz['title']
                    else:
                        bug_msg = ''
                    self.console.write("%14s : " % header, newline=False)
                    self.console.add_url(bz['id'], self.frontend.settings.bugzilla_url + bz['id'])
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
                head += cvelist[:-1].rstrip() + '\n\n'

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

    def add_page(self, key, title, widget, icon=None, tooltip=None, header=True, accel=None, callback=None):
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

class CompletedEntry(gtk.Entry):
    def __init__(self, text_col=0):
        gtk.Entry.__init__(self)
        self.text_col = text_col
        completion = gtk.EntryCompletion()
        completion.set_match_func(self.match_func)
        completion.connect("match-selected",
                            self.on_completion_match)
        completion.set_model(gtk.ListStore(str))
        completion.set_text_column(self.text_col)
        self.set_completion(completion)

    def match_func(self, completion, key, iter):
        model = completion.get_model()
        return model[iter][self.text_col].startswith(self.get_text())

    def on_completion_match(self, completion, model, iter):
        self.set_text(model[iter][self.text_col])
        self.set_position(-1)

    def add_words(self, words):
        model = self.get_completion().get_model()
        for word in words:
            model.append([word])




class StatusIcon:
    rel_font_size = 0.75
    is_working = 0
    update_count = 0

    popup_menu = None
    quit_menu = None
    search_updates_menu = None


    def __init__(self):
        self.image_checking = ICON_TRAY_WORKING
        self.image_no_update= ICON_TRAY_NO_UPDATES
        self.image_updates  = ICON_TRAY_UPDATES
        self.image_error    = ICON_TRAY_ERROR

        self.statusicon = gtk.StatusIcon()
        self.init_popup_menu()
        self.update_tray_icon()

    def init_popup_menu(self):
        menu = gtk.Menu()
        self.popup_menu = menu

        quit = gtk.MenuItem(_("Quit"))
        self.quit_menu = quit

        search_updates = gtk.MenuItem(_("Search for Updates"))
        self.search_updates_menu = search_updates
        
        menu.append(search_updates)
        menu.append(quit)
        menu.show_all()
        self.statusicon.connect("popup-menu", self.on_popup)


    def set_popup_menu_sensitivity(self, sensitive):
        self.quit_menu.set_sensitive(sensitive)
        self.search_updates_menu.set_sensitive(sensitive)
        
    def on_popup(self, icon, button, time):
        self.popup_menu.popup(None, None, gtk.status_icon_position_menu, button,
                time, self.statusicon)

    def get_status_icon(self):
        return self.statusicon

    def update_tray_icon(self):
        if self.is_working > 0:
            self.statusicon.set_tooltip_text("Yum Extender: Working")
            pixbuf = gtk.gdk.pixbuf_new_from_file(self.image_checking)
            self.set_popup_menu_sensitivity(False)
        else:
            self.set_popup_menu_sensitivity(True)
            update_count = self.update_count
            if update_count == -1:
                self.statusicon.set_tooltip_text(_("Yum Extender: Error"))
                pixbuf = gtk.gdk.pixbuf_new_from_file(self.image_error)
            elif update_count == 0:
                self.statusicon.set_tooltip_text(_("Yum Extender: No Updates"))
                pixbuf = gtk.gdk.pixbuf_new_from_file(self.image_no_update)
            else:
                self.statusicon.set_tooltip_text(_("Yum Extender: %s Updates available")
                        % update_count)
                pixbuf = self.get_pixbuf_with_text(self.image_updates,
                        str(update_count), self.rel_font_size)
        self.statusicon.set_from_pixbuf(pixbuf)
        gtk.main_iteration(False)

    # png_file must be a squared image
    def get_pixbuf_with_text(self, png_file, text, relative_font_size):
        img = cairo.ImageSurface.create_from_png(png_file)  
        size = img.get_height()
        surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, size, size)
        ctx = cairo.Context (surface)
        ctx.set_source_surface(img, 0, 0)  
        ctx.paint()

        font_size = size*relative_font_size
        ctx.set_source_rgb(0, 0, 0)
        # resize font size until text fits ...
        while font_size > 1.0:
            ctx.set_font_size(int(font_size))
            [bearing_x, bearing_y, font_x, font_y, ax, ay] = ctx.text_extents(text) 
            if font_x < size: break
            font_size = font_size * 0.9
        ctx.move_to(int(size-font_x)/2-bearing_x , int(size-font_y)/2-bearing_y)
        ctx.show_text(text)
        ctx.stroke()

        # this is ugly but the easiest way to get a pixbuf from a cairo image
        # surface...
        r = int(random.random()*999999)
        file_name = "/tmp/notifier_tmp_"+str(r)+".png"
        surface.write_to_png(file_name)
        pixbuf = gtk.gdk.pixbuf_new_from_file(file_name)
        os.remove(file_name)
        return pixbuf


    def set_update_count(self, update_count):
        '''
        set the available update count
        @param update_count: =0: no updates, -1: error occured
        '''
        self.update_count = update_count
        self.update_tray_icon()

    def set_is_working(self, is_working=True):
        '''
        set working: show a busy tray icon if is_working is True
        '''
        if is_working:
            self.is_working = self.is_working+1
        else:
            self.is_working = self.is_working-1
        self.update_tray_icon()

        
