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

import gtk
import pango

from yumexgui.gui import busyCursor, normalCursor
from yumexbase import *

class Progress:
    
    def __init__(self,ui,parent):
        self.ui = ui
        self.dialog = self.ui.Progress
        self.dialog.set_title("Working....")
        self.parent = parent
        self.dialog.set_transient_for( parent )        
        style = self.ui.packageView.get_style()
        self.ui.progressEvent.modify_bg( gtk.STATE_NORMAL, style.base[0])        
        self.progressbar = self.ui.progressBar
        self.progressbar.modify_font(SMALL_FONT)
        
        self.header = self.ui.progressHeader
        self.header.modify_font(BIG_FONT)
        self.label = self.ui.progressLabel
        self.label.modify_font(SMALL_FONT)
        self.is_active = False
        
    def show(self):
        self.is_active = True
        busyCursor(self.parent, True)
        self.reset()
        self.dialog.show_all()
        
    def hide(self):
        self.is_active = False
        normalCursor(self.parent)
        self.dialog.hide()
        
    def set_header(self,text):
        self.header.set_text(text)
        
    def set_label(self,text):
        self.label.set_text(text)
        
    def set_progress(self,fraction, text=None):
        self.progressbar.set_fraction(fraction)
        if text:
            self.progressbar.set_text(text)
            
    def pulse(self):
        self.progressbar.pulse()
        
    def reset(self):
        self.progressbar.set_fraction(0.0)
        self.progressbar.set_text("Working ...")
            
            