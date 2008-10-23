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

# Constants

from yumexbase import *



class YumexBackendDummy(YumexBackendBase):
    ''' 
    Dummy class
    
    There returns constant data there can be used for testing
    '''

    def __init__(self,frontend):
        YumexBackendBase.__init__(self,frontend)

    def setup(self):
        ''' Setup the backend'''
        self.frontend.debug('Setting up the dummy backend')

    def reset(self):
        ''' Reset the backend, so it can be setup again'''
        self.frontend.debug('Resetting the dummy backend')

    def get_packages(self, pkg_filter):
        ''' 
        get packages based on filter 
        @param pkg_filer: package list filter (Enum FILTER)
        @return: a list of packages
        '''
        self.frontend.debug('Get %s packages' % pkg_filter)
        pkgs = []
        if pkg_filter == FILTER.all:
            pkgs.append(make_dummy_pkg('dummy-a', '1.0.0', '1', 'i386'))
            pkgs.append(make_dummy_pkg('dummy-b', '1.1.1', '2', 'i386'))
            pkgs.append(make_dummy_pkg('dummy-c', '1.2.0', '3', 'i386'))
            pkgs.append(make_dummy_pkg('dummy-c', '1.2.1', '1', 'i386'))
            pkgs.append(make_dummy_pkg('dummy-d', '1.4.0', '4', 'i386'))
            pkgs.append(make_dummy_pkg('dummy-e', '1.5.0', '5', 'i386'))
            pkgs.append(make_dummy_pkg('dummy-f', '1.6.0', '6', 'i386'))
        elif pkg_filter == FILTER.installed:
            pkgs.append(make_dummy_pkg('dummy-a', '1.0.0', '1', 'i386'))
            pkgs.append(make_dummy_pkg('dummy-b', '1.1.1', '2', 'i386'))
            pkgs.append(make_dummy_pkg('dummy-c', '1.2.0', '3', 'i386'))
        elif pkg_filter == FILTER.available:
            pkgs.append(make_dummy_pkg('dummy-d', '1.4.0', '4', 'i386'))
            pkgs.append(make_dummy_pkg('dummy-e', '1.5.0', '5', 'i386'))
        elif pkg_filter == FILTER.updates:
            pkgs.append(make_dummy_pkg('dummy-c', '1.2.1', '1', 'i386'))
        elif pkg_filter == FILTER.obsoletes:
            pkgs.append(make_dummy_pkg('dummy-f', '1.6.0', '6', 'i386'))
        return pkgs
    
    def get_repositories(self):
        ''' 
        get repositories 
        @return: a list of repositories
        '''
        self.frontend.debug('Getting repository information')
        repos = []
        repos.append((True,"base","The base repo"))
        repos.append((True,"updates","The updates repo"))
        repos.append((False,"base-source","The base source repo"))
        repos.append((False,"updates-source","The updates source repo"))
        return repos

    def enable_repository(self, repoid, enabled=True):
        ''' 
        set repository enable state
        @param repoid: repo id to change
        @param enabled: repo enable state
        '''
        self.frontend.debug('Setting repository %s (Enabled = %s)' % (repoid, enabled))

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


class YumexPackageDummy(YumexPackageBase):
    '''
    This is an dummy  package object 
    '''

    def __init__(self, pkg):
        YumexPackageBase.__init__(self, pkg)

    @property
    def name(self):
        return self._pkg['name']

    @property
    def version(self):
        return self._pkg['version']

    @property
    def release(self):
        return self._pkg['release']

    @property
    def arch(self):
        return self._pkg['arch']

    @property
    def summary(self):
        return 'this is an dummy package'

    @property
    def description(self):
        return 'This is an dummy package,\n so it has only this dummy description'

    @property
    def changelog(self):
        clog = []
        clog.append(('Tue Dec 7 2004','Tim Lauridsen <tla@rasmil.dk>','bump version to 0.1.1'))
        clog.append(('Fri Dec 8 2004','Tim Lauridsen <tla@rasmil.dk>','bump version to 0.1.2'))
        clog.append(('Sat Dec 9 2004','Tim Lauridsen <tla@rasmil.dk>','bump version to 0.1.3'))
        return clog    

    @property
    def filelist(self):
        flist = []
        flist.append('/usr/share/dummy')
        flist.append('/usr/share/dummy/dummy.png')
        flist.append('/etc/dummy.conf')
        flist.append('/usr/bin/dummy')
        return flist

    @property
    def id(self):
        return "%s-%s.%s.%s" % (self.name, self.version, self.release, self.arch)

    @property
    def filename(self):
        return "%s-%s.%s.%s.rpm" % (self.name, self.version, self.release, self.arch)

class YumexTransactionDummy:
    '''
    Yumex Transaction Base class

    This is a abstract transaction queue for storing unprocessed changes
    to the system and to process the transaction on the system.
    '''

    def __init__(self, backend, frontend):
        self._backend = backend
        self._frontend = frontend

    def add(self, po):
        pass

    def remove(self, po):
        pass

    def has_item(self, po):
        pass

    def add_group(self, grp):
        pass

    def remove_group(self, grp):
        pass

    def has_group(self, grp):
        pass

    def process_transaction(self):
        pass


def make_dummy_pkg(name,ver,rel,arch):
    pkg = {}
    pkg['name'] = name
    pkg['version'] = ver    
    pkg['release'] = rel
    pkg['arch'] = arch
    ypo = YumexPackageDummy(pkg)
    return ypo               