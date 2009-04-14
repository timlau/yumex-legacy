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

# Imports

from yumexbase import *
from yumexbackend import YumexBackendBase, YumexPackageBase, YumexTransactionBase
from yumexbackend.yum_clientserver import YumClient

               
class YumexBackendYum(YumexBackendBase,YumClient):
    ''' Yumex Backend Yume class

    This is the base class to interact with yum
    '''

    def __init__(self, frontend):
        transaction = YumexTransactionYum(self,frontend)
        YumexBackendBase.__init__(self, frontend,transaction)
        YumClient.__init__(self)

    # Overload the YumClient message methods
        
    def error(self,msg):
        """ error message """
        self.frontend.error(msg)

    def warning(self,msg):
        """ warning message """
        self.frontend.warning(msg)

    def info(self,msg):
        """ info message """
        self.frontend.info(msg)
    
    def debug(self,msg):
        """ debug message """
        self.frontend.debug(msg)

    def yum_logger(self,msg):
        """ yum logger message """
        self.frontend.info("YUM: "+ msg)

    def timeout(self):
        """ 
        timeout function call every time an timeout occours
        An timeout occaurs if the server takes more then timeout
        periode to respond to the current action.
        the default timeout is .5 sec.
        """
        self.frontend.timeout()
        
    def exception(self,msg):
        """ debug message """
        self.frontend.exception(msg)

    def setup(self):
        ''' Setup the backend'''
        YumClient.setup(self)
        
    def reset(self):
        ''' Reset the backend, so it can be setup again'''
        YumClient.reset(self)

    def get_packages(self, pkg_filter):
        ''' 
        get packages based on filter 
        @param pkg_filer: package list filter (Enum FILTER)
        @return: a list of packages
        '''
        self.frontend.debug('Get %s packages' % pkg_filter)
        pkgs = YumClient.get_packages(self,pkg_filter)
        return [YumexPackageYum(p) for p in pkgs]

    def get_repositories(self):
        ''' 
        get repositories 
        @return: a list of repositories
        '''
        self.frontend.debug('Getting repository information')
        repos = YumClient.get_repos(self)
        return repos


    def enable_repository(self, repoid, enabled=True):
        ''' 
        set repository enable state
        @param repoid: repo id to change
        @param enabled: repo enable state
        '''
        self.frontend.debug('Setting repository %s (Enabled = %s)' % (repoid, enabled))
        repo = YumClient.enable_repo(self,repoid,enabled)
        return repo

    def get_groups(self):
        ''' 
        get groups 
        @return: a list of groups
        '''
        self.frontend.debug('Getting Group information')

    def get_group_packages(self, group, grp_filter):
        ''' 
        get packages in a group 
        @param group: group id to get packages from
        @param grp_filter: group filters (Enum GROUP)
        '''
        self.frontend.debug('Getting packages in group : %s (FILTER = %s)' % (group, grp_filter))

    def search(self, keys, sch_filters):
        ''' 
        get packages matching keys
        @param keys: list of keys to seach for
        @param sch_filters: list of search filter (Enum SEARCH)
        '''
        self.frontend.debug('Seaching for %s in %s ' % (keys, sch_filters))
        pkgs = YumClient.search(self,keys, sch_filters)
        return [self.frontend.package_cache.find(po) for po in pkgs]



class YumexPackageYum(YumexPackageBase):
    '''
    Yumex Package Base class

    This is an abstract package object for a package in the package system
    '''

    def __init__(self, pkg):
        YumexPackageBase.__init__(self, pkg)
        self.queued = False
        self.selected = False
        self.visible = True

    def set_select( self, state ):
        self.selected = state

    def set_visible( self, state ):
        self.visible = state
        
    def __str__(self):
        return str(self._pkg)

    @property
    def name(self):
        return self._pkg.name

    @property
    def version(self):
        return self._pkg.ver

    @property
    def release(self):
        return self._pkg.rel

    @property
    def epoch(self):
        return self._pkg.epoch

    @property
    def arch(self):
        return self._pkg.arch

    @property
    def action(self):
        return self._pkg.action

    @property
    def color(self):
        return 'black'

    @property
    def repoid(self):
        return self._pkg.repoid

    @property
    def action(self):
        return self._pkg.action

    @property
    def summary(self):
        return self._pkg.summary

    @property
    def size(self):
        return format_number(long(self._pkg.size))

    @property
    def description(self):
        return self._pkg.get_attribute('description')

    @property
    def changelog(self):
        return self._pkg.get_attribute('changelog')

    @property
    def filelist(self):
        return self._pkg.get_attribute('filelist') 

    @property
    def recent(self):
        return self._pkg.recent == '1'

    @property        
    def id(self):        
        return '%s\t%s\t%s\t%s\t%s\t%s' % (self.name,self.epoch,self.version,self.release,self.arch,self.repoid)

    @property
    def filename(self):
        return "%s-%s.%s.%s.rpm" % (self.name, self.version, self.release, self.arch)

class YumexTransactionYum(YumexTransactionBase):
    '''
    Yumex Transaction Base class

    This is a abstract transaction queue for storing unprocessed changes
    to the system and to process the transaction on the system.
    '''

    def __init__(self, backend, frontend):
        '''
        initialize the transaction queue
        @param backend: The current YumexBackend
        @param frontend: the current YumexFrontend
        '''
        YumexTransactionBase.__init__(self, backend, frontend)

    def add(self, po, action):
        '''
        add a package to the queue
        @param po: package to add to the queue
        '''
        self.backend.add_transaction(po.id, action)

    def remove(self, po):
        '''
        remove a package from the queue
        @param po: package to remove from the queue
        '''
        self.backend.remove_transaction(po.id)

    def has_item(self, po):
        '''
        check if a package is already in the queue
        @param po: package to check for
        '''
        pass

    def add_group(self, grp):
        '''
        Add a group to the queue
        @param grp: group to add to queue
        '''
        pass

    def remove_group(self, grp):
        '''
        Remove a group from the queue
        @param grp: group to add to queue
        '''
        pass

    def has_group(self, grp):
        '''
        Check if a group is in the  queue
        @param grp: group to check for
        '''
        pass
    
    def process_transaction(self):
        '''
        Process the packages and groups in the queue
        '''
        self.backend.run_transaction()
        
    def get_transaction_packages(self):
        '''
        Get the current packages in the transaction queue
        '''
        pkgs = self._backend.list_transaction()
        return [YumexPackageYum(p) for p in pkgs]
    
    
# from output.py (yum)
def format_number(number, SI=0, space=' '):
    """Turn numbers into human-readable metric-like numbers"""
    symbols = ['', # (none)
                'k', # kilo
                'M', # mega
                'G', # giga
                'T', # tera
                'P', # peta
                'E', # exa
                'Z', # zetta
                'Y'] # yotta

    if SI: step = 1000.0
    else: step = 1024.0

    thresh = 999
    depth = 0

    # we want numbers between 
    while number > thresh:
        depth = depth + 1
        number = number / step

    # just in case someone needs more than 1000 yottabytes!
    diff = depth - len(symbols) + 1
    if diff > 0:
        depth = depth - diff
        number = number * thresh ** depth

    if type(number) == type(1) or type(number) == type(1L):
        format = '%i%s%s'
    elif number < 9.95:
        # must use 9.95 for proper sizing.  For example, 9.99 will be
        # rounded to 10.0 with the .1f format string (which is too long)
        format = '%.1f%s%s'
    else:
        format = '%.0f%s%s'

    return(format % (number, space, symbols[depth]))
    