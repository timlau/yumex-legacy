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
from yumexbase.i18n import _, P_
# pylint: enable-msg=W0611

from yum.config import *

from optparse import OptionParser
from iniparse.compat import ConfigParser,SafeConfigParser


class YumexConf( BaseConfig ):
    """ Yum Extender Config Setting"""
    autorefresh = BoolOption( True )
    recentdays = IntOption( 14 )
    debug = BoolOption( False )
    plugins = BoolOption( True)
    proxy = Option()
    repo_exclude = ListOption(['debug','source'])
    yumdebuglevel = IntOption( 2 )
    color_install = Option( 'darkgreen' )
    color_update = Option( 'red' )
    color_normal = Option( 'black' )
    color_obsolete = Option( 'blue' )
    disable_repo_page = BoolOption( False )
    branding_title = Option('Yum Extender NextGen')

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

    def get_yumex_config(self,configfile='/etc/yumex.conf', sec='yumex' ):
        conf = YumexConf()
        parser = ConfigParser()    
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
        parser.add_option("-d", "--debug",
                        action="store_true", dest="debug", default=self.settings.debug,
                        help="Debug mode")
        parser.add_option("", "--noplugins",
                        action="store_false", dest="plugins", default=self.settings.plugins,
                        help="Disable yum plugins")
        parser.add_option("-n", "--noauto",
                        action="store_false", dest="autorefresh", default=self.settings.autorefresh,
                        help="No automatic refresh af program start")
        parser.add_option("", "--debuglevel", dest="yumdebuglevel", action="store",
                default=self.settings.yumdebuglevel, help="yum debugging output level", type='int',
                metavar='[level]')      
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
        options = ['plugins', 'debug', 'yumdebuglevel','autorefresh']
        for opt in options:
            self._calcOption(opt)
            
        
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
        
    def save(self, configfile='/etc/yumex.conf'):
        fn = open(configfile,"w")
        self.conf_settings.write(fn)
        fn.close()
