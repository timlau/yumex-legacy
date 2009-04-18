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


# General purpose GUI helper classes

import gtk
import gtk.glade
import pango
import logging
import types
import sys

class TextViewBase:
    '''  Encapsulate a gtk.TextView with support for adding and using pango styles'''
    def __init__(self, textview):
        '''
        Setup the textview
        @param textview: the gtk.TextView widget to use 
        '''
        self.textview = textview
        self.buffer = self.textview.get_buffer()
        self.endMark = self.buffer.create_mark("End", self.buffer.get_end_iter(), False)
        self.startMark = self.buffer.create_mark("Start", self.buffer.get_start_iter(), False)
        self._styles = {}
        self.default_style = None # the default style (text tag)
            
    def add_style(self,tag,style):
        '''
        Add a new pango style
        @param tag: text tag to indentify the style
        @param style: the gtk.TextTag containing the style
        '''
        self._styles[tag] = style
        self.buffer.get_tag_table().add(self._styles[tag])        
                
    def get_style(self,tag=None):
        '''
        Get a gtk.TextTag style
        @param tag: the tag of the style to get 
        '''
        if not tag:
            tag = self.default_style
        if tag in self._styles:
            return self._styles[tag]
        else:
            return None
        
    def change_style(self,tag, color, font):
        '''
        Change the font and color of a gtk.TextTag style
        @param tag: text tag to indentify the style
        @param color: the font foreground color name ex. 'red'
        @param font: the font name ex. 'courier' 
        '''
        style = self.get_style(tag)
        if style:    
            style.set_property("foreground", color)
            style.set_property("font", font)
    
    def write(self, txt, style=None, newline=True):
        ''' 
        write a line of text to the textview and scoll to end
        @param txt: Text to write to textview
        @param style: text tag to indentify the style to use
        @param newline: if True, then add newline to the text it not there already
        '''
        if not txt: 
            return
        txt = toUTF(txt) # Convert the text to UTF-8
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
        '''
        clear the textview
        '''
        self.buffer.set_text('')
        
    def goTop(self):
        '''
        Set the cursor to the start of the text view
        '''
        self.textview.scroll_to_iter(self.buffer.get_start_iter(), 0.0)
    
    
class TextViewConsole(TextViewBase):
    '''  
    A textview console with 3 predefined styles
    'info' (blue) , 'debug'  and 'error' (red)
    @param textview: the gtk.TextView widget to use
    @param text_size: Optional text_size for the styles (default = 8)  
    '''
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
            elif record.levelno <= 40:
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
            raise AttributeError("Can't find widget %s in %s.\n" % (name, self.filename))
        
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
        self.quit()
        try:
            gtk.main_quit()
        except:
            pass
        sys.exit(0)
        
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
    ''' Setup Python logging using a TextViewLogHandler '''
    logger = logging.getLogger(logroot)
    logger.setLevel(loglvl)
    formatter = logging.Formatter(logfmt, "%H:%M:%S")
    handler = TextViewLogHandler(console)
    handler.setFormatter(formatter)
    handler.propagate = False
    logger.addHandler(handler)
    return handler
    
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

