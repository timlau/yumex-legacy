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

import gtk
import gtk.glade
import pango
import logging
import types
from yumexbase.i18n import _
from yumexbase import *
from yumexbackend.yum_backend import YumexPackageYum


#
# Classses
#
        
        
class PackageCache:
    def __init__(self,backend):
        self._cache = {}
        self.backend = backend
        
    def reset(self):
        del self.cache
        self._cache = {}

    def get_packages(self,filter):
        if not str(filter) in self._cache:
            self._cache[str(filter)] = self.backend.get_packages(filter)
        return self._cache[str(filter)]
    
    def find(self,po):
        if po.action == 'u':
            target = self._cache[str(FILTER.updates)]
        elif po.action == 'i':
            target = self._cache[str(FILTER.available)]
        else:
            target = self._cache[str(FILTER.installed)]
        for pkg in target:
            if str(po) == str(pkg):   
                return pkg
        return YumexPackageYum(po)
    
class TextViewBase:
    '''  Encapsulate a gtk.TextView'''
    def __init__(self, textview,):
        self.textview = textview
        self.buffer = self.textview.get_buffer()
        self.endMark = self.buffer.create_mark("End", self.buffer.get_end_iter(), False)
        self.startMark = self.buffer.create_mark("Start", self.buffer.get_start_iter(), False)
        self._styles = {}
        self.default_style = None
            
    def add_style(self,tag,style):
        self._styles[tag] = style
        self.buffer.get_tag_table().add(self._styles[tag])        
                
    def get_style(self,tag=None):
        if not tag:
            tag = self.default_style
        if tag in self._styles:
            return self._styles[tag]
        else:
            return None
        
    def change_style(self,tag, color, font):
        style = self.get_style(tag)
        if style:    
            style.set_property("foreground", color)
            style.set_property("font", font)
    
    def write(self, txt, style=None, newline=True):
        """ write a line to button of textview and scoll to end
        @param txt: Text to write to textview
        @param style: name tag for the pango style to use. 
        """
        txt = toUTF(txt)
        if newline and txt[-1] != '\n':
            txt += '\n'
        start, end = self.buffer.get_bounds()
        style = self.get_style(style)
        if style:
            self.buffer.insert_with_tags(end, txt, style)
        else:            
            self.buffer.insert(end, txt)
        self.textview.scroll_to_iter(self.buffer.get_end_iter(), 0.0)
        doGtkEvents()

    def clear(self):
        self.buffer.set_text('')
        
    def goTop(self):
        self.textview.scroll_to_iter(self.buffer.get_start_iter(), 0.0)
    
    
class TextViewConsole(TextViewBase):
    '''  Encapsulate a gtk.TextView'''
    def __init__(self, textview,font_size=8):
        TextViewBase.__init__(self,textview)
        # info style
        style = gtk.TextTag("info")
        style.set_property("foreground", "midnight blue")
        style.set_property("family", "Monospace")
        style.set_property("size_points", font_size)
        self.add_style('info', style)
        self.default_style = 'info'

        # debug style
        style = gtk.TextTag("debug")
        style.set_property( "foreground", "DarkOrchid4" )
        style.set_property("family", "Monospace")
        style.set_property("size_points", font_size)
        self.add_style('debug', style)

        # error style
        style = gtk.TextTag("error")
        style.set_property("foreground", "red")
        style.set_property("family", "Monospace")
        style.set_property("style", pango.STYLE_ITALIC)
        style.set_property("size_points", font_size)
        self.add_style('error', style)
    
        

class TextViewLogHandler(logging.Handler):
    ''' Python logging handler for writing in a TextViewConsole'''
    def __init__(self, console, doGTK=False):
        logging.Handler.__init__(self)
        self.console = console
        self.doGTK = doGTK
        
        
    def emit(self, record):   
        msg = self.format(record)
        if self.console:
            if self.doGTK:
                doGtkEvents()
            if record.levelno < 20: 
                self.console.write(msg, 'debug')
            elif ecord.levelno <= 40:
                self.console.write(msg, 'info')                
            else:
                self.console.write(msg, 'error')  
    

class UI(gtk.Builder):
    """Base class for UIs loaded from a gtk.Builder xml file"""
    
    def __init__(self, filename, rootname, domain = None):
        """Initialize a new instance.
        `filename' is the name of the gtk.Builder .xml file containing the UI hierarchy.
        `rootname' is the name of the topmost widget to be loaded.
        `domain' is a optional translation domain"""
        
        gtk.Builder.__init__(self)
        self.filename = filename
        self.add_from_file(filename)
        self.root = self.get_object(rootname)
        if domain:
            self.set_translation_domain(domain)

    def __getattr__(self, name):
        """Look up an as-yet undefined attribute, assuming it's a widget."""
        result = self.get_object(name)
        if result is None:
            raise AttributeError("Can't find widget %s in %s.\n" %
                                 (`name`, `self.filename`))
        
        # Cache the widget to speed up future lookups.  If multiple
        # widgets in a hierarchy have the same name, the lookup
        setattr(self, name, result)
        return result

class Controller:
    """Base class for all controllers of gtk.Builder UIs."""
    
    def __init__(self, filename, rootname, domain = None):
        """Initialize a new instance.
        `ui' is the user interface to be controlled."""
        self.ui = UI(filename, rootname, domain)
        self.ui.connect_signals(self._getAllMethods())
        self.window = getattr(self.ui,rootname)
        self.window.connect( "delete_event", self.main_quit )

    def main_quit(self, widget=None, event=None ):
        ''' Main destroy Handler '''
        self.quit
        gtk.main_quit()
        
    def quit(self):
        ''' Virtuel quit handler to be overloaded in child class'''
        pass        

    def _getAllMethods(self):
        """Get a dictionary of all methods in self's class hierarchy."""
        result = {}

        # Find all callable instance/class attributes.  This will miss
        # attributes which are "interpreted" via __getattr__.  By
        # convention such attributes should be listed in
        # self.__methods__.
        allAttrNames = self.__dict__.keys() + self._getAllClassAttributes()
        for name in allAttrNames:
            value = getattr(self, name)
            if callable(value):
                result[name] = value
        return result

    def _getAllClassAttributes(self):
        """Get a list of all attribute names in self's class hierarchy."""
        nameSet = {}
        for currClass in self._getAllClasses():
            nameSet.update(currClass.__dict__)
        result = nameSet.keys()
        return result

    def _getAllClasses(self):
        """Get all classes in self's heritage."""
        result = [self.__class__]
        i = 0
        while i < len(result):
            currClass = result[i]
            result.extend(list(currClass.__bases__))
            i = i + 1
        return result

        
    
#
# Functions
#    

def doLoggerSetup(console, logroot, logfmt='%(message)s', loglvl=logging.DEBUG):
    logger = logging.getLogger(logroot)
    logger.setLevel(loglvl)
    formatter = logging.Formatter(logfmt, "%H:%M:%S")
    handler = TextViewLogHandler(console)
    handler.setFormatter(formatter)
    handler.propagate = False
    logger.addHandler(handler)
    
def busyCursor(mainwin, insensitive=False):
    ''' Set busy cursor in mainwin and make it insensitive if selected '''
    mainwin.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
    if insensitive:
        mainwin.set_sensitive(False)
    doGtkEvents()

def normalCursor(mainwin):
    ''' Set Normal cursor in mainwin and make it sensitive '''
    if mainwin.window != None:
        mainwin.window.set_cursor(None)
        mainwin.set_sensitive(True)        
    doGtkEvents()
    
def doGtkEvents():
    while gtk.events_pending():      # process gtk events
        gtk.main_iteration()


def toUTF(txt):
    rc = ""
    if isinstance(txt, types.UnicodeType):
        return txt
    else:
        try:
            rc = unicode(txt, 'utf-8')
        except UnicodeDecodeError, e:
            rc = unicode(txt, 'iso-8859-1')
        return rc


class PageHeader(gtk.HBox):
    ''' Page header to show in top of Notebook Page'''
    
    def __init__(self,text,icon=None):
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
        self.label.set_padding(10,0)
        # Setup Icon
        self.icon = gtk.Image()
        if icon:
            self.icon.set_from_file(icon)
        else:
            self.icon.set_from_icon_name('gtk-dialog-info',6)
        self.pack_start(self.label,expand=False)
        self.pack_end(self.icon,expand=False)
        self.show_all()
        
class PageSelector:
    ''' Button notebook selector '''
    
    def __init__(self,content,notebook):
        ''' setup the selector '''
        self.content = content
        self.notebook = notebook
        self._buttons = {}
        self._first = None
        self._selected = None
        
        
    def add_button(self,key,icon=None,tooltip=None):
        ''' Add a new selector button '''
        if len(self._buttons) == 0:
            button = gtk.RadioButton( None )
            self._first = button
        else:
            button = gtk.RadioButton( self._first )
        button.connect( "clicked", self.on_button_clicked, key )
    
        button.set_relief( gtk.RELIEF_NONE )
        button.set_mode( False )
    
        if icon:
            p = gtk.gdk.pixbuf_new_from_file( icon )
            pix = gtk.Image()
            pix.set_from_pixbuf( p )
            pix.show()
            button.add(pix)
    
        if tooltip:
            self.tooltip.set_tip(button,text)
        button.show()
        self.content.pack_start( button, False )
        self._buttons[key] = button

    def set_active(self,key):
        ''' set the active selector button '''
        if key in self._buttons:
            button = self._buttons[key]
            button.set_active(True)
            
    def get_active(self):
        ''' get the active selector button'''
        return self._selected            
            
    def on_button_clicked(self, widget=None, key=None ):
        ''' button clicked callback handler'''
        if widget.get_active(): # only work on the active button
            self.notebook._set_page(key) # set the new notebook page
            self._selected = key
            
class Notebook:
    ''' Notebook with button selector '''
    
    def __init__(self,notebook,selector):
        ''' setup the notebook and the selector '''
        self.notebook = notebook
        self.selector = PageSelector(selector,self)
        self._pages = {}

    def add_page(self, key, title, widget, icon=None, tooltip=None, header=True):
        ''' 
        Add a new page and selector button to notebook
        @param key: the page key (name) used by reference the page
        @param widget: the widget container to insert into the page
        @param icon: an optional icon file for the selector button
        @param tooltip: an optional tooltip for the selector button  
        '''
        num = len(self._pages)
        container = gtk.VBox()
        self._pages[key] = (num,container)
        if header:
            header = PageHeader(title,icon)
            container.pack_start(header,expand=False,padding=5)
            sep = gtk.HSeparator()
            sep.show()
            container.pack_start(sep,expand=False)
        # get the content from the widget and reparent it and add it to page    
        content = gtk.VBox()
        widget.reparent(content)
        container.pack_start(content,expand=True)
        content.show()
        container.show()
        self.notebook.append_page(container)
        # Add selector button
        self.selector.add_button(key, icon, tooltip)
        
    def set_active(self,key):
        '''
        set the active page in notebook and selector
        @param key: the page key (name) used by reference the page
        '''
        self.selector.set_active(key)
        
    def _set_page(self,key):
        '''
        set the current notebook page
        '''
        if key in self._pages:
            num,widget = self._pages[key]
            self.notebook.set_current_page(num)
    
