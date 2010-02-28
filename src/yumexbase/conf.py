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
"""
 Yum Extender Configuration and Command line option classes
"""
# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
import logging
import os
import shutil
#from yumexbase.i18n import _, P_
# pylint: enable-msg=W0611

from yum.config import *
#from yumexbase.constants import *

from optparse import OptionParser
from iniparse.compat import ConfigParser


class YumexConf( BaseConfig ):
    """ Yum Extender Config Setting"""
    autorefresh = BoolOption( True )
    recentdays = IntOption( 14 )
    debug = BoolOption( False )
    plugins = BoolOption( True)
    proxy = Option('')
    repo_exclude = ListOption(['debug','source'])
    yumdebuglevel = IntOption( 2 )
    color_install = Option( 'darkgreen' )
    color_update = Option( 'red' )
    color_normal = Option( 'black' )
    color_obsolete = Option( 'blue' )
    disable_repo_page = BoolOption( False )
    branding_title = Option('Yum Extender NextGen')
    win_width = IntOption( 1000)
    win_height = IntOption( 600 ) 
    win_sep = IntOption( 300 ) 
    history_limit = IntOption(15)
    disable_netcheck = BoolOption( False )
    yum_conf = Option( '/etc/yum.conf' )
    use_sortable_view = BoolOption( False )
    

class YumexOptions:

    def __init__(self):
        self.logger = logging.getLogger('yumex.YumexOptions')
        self.conf_settings = self.get_yumex_config()
        self.settings = self.get_yumex_config()
        self._optparser = OptionParser()
        (self.cmd_options, self.cmd_args) = self.setupParser()
        self.update_settings()

    def get_cmd_options(self):    
        return (self.cmd_options, self.cmd_args)

    def get_yumex_config(self,configfile='.yumex.conf', sec='yumex' ):
        conf = YumexConf()
        parser = ConfigParser()    
        configfile=os.environ['HOME']+"/"+configfile
        if not os.path.exists(configfile):
            # if /etc/yumex.conf exists and is readable the copy it to homedir
            if os.path.exists('/etc/yumex.conf') and os.access("/etc/yumex.conf", os.R_OK):
                shutil.copyfile('/etc/yumex.conf', configfile)
        parser.read( configfile )
        if not parser.has_section('yumex'):
            parser.add_section('yumex')
        conf.populate( parser, sec )
        return conf
    
    def reload(self):
        self.conf_settings = self.get_yumex_config()
        self.settings = self.get_yumex_config()
        self.update_settings()

    def setupParser(self):
        parser = self._optparser
        parser.add_option("", "--root",
                        action="store_true", dest="root", default=False,
                        help="Run as root")
        parser.add_option("", "--disable-netcheck",
                        action="store_true", dest="disable_netcheck", default=False,
                        help="Disable the automatic network connection check")
        parser.add_option("-d", "--debug",
                        action="store_true", dest="debug", default=self.settings.debug,
                        help="Debug mode")
        parser.add_option("", "--noplugins",
                        action="store_false", dest="plugins", default=self.settings.plugins,
                        help="Disable yum plugins")
        parser.add_option("", "--win-size",
                        dest="win_size", action="store", type='string',
                        help="Set size of window (h = height, w = widght)", metavar='[wxh]')
        parser.add_option("-n", "--noauto",
                        action="store_false", dest="autorefresh", default=self.settings.autorefresh,
                        help="No automatic refresh af program start")
        parser.add_option("", "--debuglevel", dest="yumdebuglevel", action="store",
                default=self.settings.yumdebuglevel, help="yum debugging output level", type='int',
                metavar='[level]')      
        parser.add_option("-c", "", dest="yum_conf", action="store", 
                default='/etc/yum.conf', help="yum config file to use default = /etc/yum.conf",
                metavar=' [config file]')
        
        return parser.parse_args()

    def dump(self):
        print("Current Settings")
        settings = str( self.settings ).split( '\n' )
        for s in settings:
            if not s.startswith( '[' ):
                print("    %s" % s )
        
    def update_settings( self ):
        """ update setting with commandline options """
        #options = ['plugins', 'debug', 'usecache', 'fullobsoletion','nolauncher']
        options = ['plugins', 'debug', 'yumdebuglevel','autorefresh','disable_netcheck','yum_conf']
        for opt in options:
            self._calcOption(opt)
        self._check_win_size()
            
    def _check_win_size(self):        
        if self.cmd_options.win_size:
            size = self.cmd_options.win_size
            if 'x' in size:
                s = size.split('x')
                w = int(s[0])
                h = int(s[1])
                if w > 635 and h > 351: # Check for min size 
                    self.settings.win_width = w
                    self.settings.win_height = h
                
        
    def _calcOption(self,option):
        '''
        Check if a command line option has a diffent value, than
        the default value for the setting.
        if it is the set the setting value to the value from the 
        commandline option.
        '''
        default = None
        cmdopt = getattr( self.cmd_options, option )
        if self.settings.isoption(option):
            optobj = self.settings.optionobj(option)
            default = optobj.default
        if cmdopt != default:
            setattr( self.settings, option,cmdopt)
        
    def save(self, configfile='.yumex.conf'):
        configfile=os.environ['HOME']+"/"+configfile
        fn = open(configfile,"w")
        self.conf_settings.write(fn)
        fn.close()
