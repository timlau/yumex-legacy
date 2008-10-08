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

from enum import Enum

# Package Types
PKG_TYPE    = Enum('installed','available','update','obsolete')
# Package list filters
FILTER      = Enum('all','installed','available','updates','obsoletes')
# Search filters
SEARCH      = Enum('name','summary','description','ver','arch','repoid')
# Group Package filters
GROUP       = Enum('all','minimum')
# State
STATE       = Enum('none','init','download-meta','download-pkg','update','install','remove','cleanup')

class YumexBackendBase:
    ''' Yumex Backend Base clasee

    This is the base class to interact with the package system
    '''

    def __init__(self):
        pass

    def setup(self):
        ''' Setup the backend'''
        pass

    def reset(self):
        ''' Reset the backend, so it can be setup again'''
        pass

    def get_packages(self,filter):
        pass

    def get_repositories(self):
        pass

    def enable_repository(self,repoid,enabled=True):
        pass

    def get_categories(self):
        pass

    def get_groups(self,cat_id = None):
        pass

    def get_group_packages(self,filter):
        pass

    def search(self,keys,filters):
        pass


class YumexFrontendBase:
    '''
    Yumex Front Base class

    This is a frontend callback class used by the backend and
    transaction to notify the frontend about changes.
    '''

    def __init__(self,backend,progress):
        self._backend = backend
        self._progress = progress

    def set_state(self,state):
        pass

    def get_progress(self):
        return self._progress

    def progress(self):
        pass

    def confirm_transaction(self,transaction):
        pass

    def error(self,msg):
        pass

    def info(self,msg):
        pass

    def debug(self,msg):
        pass

    def warning(self,msg):
        pass

    def reset(self):
        pass


class YumexPackageBase:
    '''
    Yumex Package Base class

    This is an abstract package object for a package in the package system
    '''

    def __init__(self,pkg):
        self._pkg = pkg
        self.selected = False

    @property
    def name(self):
        pass

    @property
    def version(self):
        pass

    @property
    def release(self):
        pass

    @property
    def arch(self):
        pass

    @property
    def summary(self):
        pass

    @property
    def description(self):
        pass

    @property
    def changelog(self):
        pass

    @property
    def filelist(self):
        pass

    @property
    def id(self):
        return "%s-%s.%s.%s" % (self.name,self.version,self.release,self.arch)

    @property
    def filename(self):
        return "%s-%s.%s.%s.rpm" % (self.name,self.version,self.release,self.arch)

class YumexTransactionBase:
    '''
    Yumex Transaction Base class

    This is a abstract transaction queue for storing unprocessed changes
    to the system and to process the transaction on the system.
    '''

    def __init__(self,backend,frontend):
        self._backend = backend
        self._frontend = frontend

    def add(self,po):
        pass

    def remove(self,po):
        pass

    def has_item(self,po):
        pass

    def add_group(self,grp):
        pass

    def remove_group(self,grp):
        pass

    def has_group(self.grp):
        pass

    def process_transaction(self):
        pass

    def get_transaction_packages(self):
        pass

class YumexProgressElememt:
    '''
    '''

    def __init__(self,name,size):
        self.name = name
        self.size = size
        self.downloaded = 0L
        self.eta = 0L
        self.speed = 0L

    def reset(self):
        self.downloaded = 0L
        self.ETA = 0L
        self.speed = 0L

    def set_progress(downloaded,eta,speed):
        self.downloaded = downloaded
        self.eta = eta
        self.speed = speed

class YumexProgressBase:
    '''
    Yumex Progress Base class

    This is a actract progress class to store the current progress
    '''

    def __init__(self):
        self._names = {}
        self._current = None

    def set_names(self,names):
        self._names = {}
        for pkg in names:
            self._names[pkg.name] = pkg


    def set_current(self,current):
        self._current = current

    def get_current(self):
        return self._current






