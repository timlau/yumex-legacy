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
'''


import gtk
import pango
import gobject

from guihelpers import busyCursor, normalCursor
from yumexbase import YumexProgressBase
from yumexbase.constants import *


# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
import logging
from yumexbase.i18n import _, P_
# pylint: enable-msg=W0611


class Progress(YumexProgressBase):
    '''
    
    '''
    
    def __init__(self, ui, parent):
        '''
        
        @param ui:
        @param parent:
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
        
    def show(self):
        '''
        
        '''
        self._active = True
        busyCursor(self.parent, True)
        self.reset()
        self.dialog.show_all()
        
    def hide(self):
        '''
        
        '''
        self._active = False
        normalCursor(self.parent)
        self.dialog.hide()

    def set_title(self, text):
        '''
        
        @param text:
        '''
        self.dialog.set_title(text)
        
    def set_header(self, text):
        '''
        
        @param text:
        '''
        self.header.set_text(text)
        self.set_action("")
        
    def set_action(self, text):
        '''
        
        @param text:
        '''
        self.label.set_markup(text)
        
    def set_fraction(self, frac, text = None):
        '''
        
        @param frac:
        @param text:
        '''
        self.progressbar.set_fraction(frac)
        if text:
            self.progressbar.set_text(text)
            
    def pulse(self):
        '''
        
        '''
        self.progressbar.set_text(_("Working !!!"))
        self.progressbar.pulse()
        
    def reset(self):
        '''
        
        '''
        self.progressbar.set_fraction(0.0)
        self.progressbar.set_text("")
            
class TransactionConfirmation:
    '''
    '''
    
    def __init__(self, ui, parent):
        '''
        
        @param ui:
        @param parent:
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
        
        '''
        self.dialog.show_all()
        self.view.expand_all()
        rc = self.dialog.run()
        return rc == 1

    def destroy(self):
        '''
        
        '''
        self.dialog.hide()

        
    def set_header(self, text):
        '''
        
        @param text:
        '''
        self.header.set_text(text)
        
    def setup_view(self, view):
        '''
        
        @param view:
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

    def create_text_column(self, hdr, view, colno, min_width = 0):
        '''
        
        @param hdr:
        @param view:
        @param colno:
        @param min_width:
        '''
        cell = gtk.CellRendererText()    # Size Column
        column = gtk.TreeViewColumn(hdr, cell, markup = colno)
        column.set_resizable(True)
        if not min_width == 0:
            column.set_min_width(min_width)
        view.append_column(column)        
             
             
    def populate(self, pkglist):
        '''
        
        @param pkglist:
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
    '''
    
    def __init__(self, ui, parent, title, text, longtext, modal):
        '''
        
        @param ui:
        @param parent:
        @param title:
        @param text:
        @param longtext:
        @param modal:
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
        
        @param text:
        '''
        self.text.set_markup(text)
    
    def set_long_text(self, longtext):
        '''
        
        @param longtext:
        '''
        buf = self.longtext.get_buffer()
        start, end = buf.get_bounds()
        buf.insert_with_tags(end, longtext, self.style_err)
        
    def run(self):
        '''
        
        '''
        self.dialog.show_all()
        return self.dialog.run()

    def destroy(self):
        '''
        
        '''
        self.dialog.hide()

def okDialog(parent, msg):
    '''
    
    @param parent:
    @param msg:
    '''
    dlg = gtk.MessageDialog(parent = parent,
                            type = gtk.MESSAGE_INFO,
                            buttons = gtk.BUTTONS_OK)
    dlg.set_markup(cleanMarkupSting(msg))
    rc = dlg.run()
    dlg.destroy()

def questionDialog(parent, msg):
    '''
    
    @param parent:
    @param msg:
    '''
    dlg = gtk.MessageDialog(parent = parent,
                            type = gtk.MESSAGE_QUESTION,
                            buttons = gtk.BUTTONS_YES_NO)
    dlg.set_markup(cleanMarkupSting(msg))
    rc = dlg.run()
    dlg.destroy()
    if rc == gtk.RESPONSE_YES:
        return True
    else:
        return False
    
def cleanMarkupSting(msg):
    '''
    
    @param msg:
    '''
    msg = str(msg) # make sure it is a string
    msg = gobject.markup_escape_text(msg)
    return msg
            