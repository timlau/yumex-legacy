


class YumexBackendBase(object):
    '''
    Yumex Backend Base class
    This is the base class to interact with the package system    
    '''
    def __init__(self, frontend, transaction):
        ''' 
        init the backend 
        @param frontend: the current frontend
        '''
        self.frontend = frontend
        self.transaction = transaction

    def setup(self, repos = []):
        ''' Setup the backend'''
        raise NotImplementedError()

    def reset(self):
        ''' Reset the backend, so it can be setup again'''
        raise NotImplementedError()

    def get_packages(self, pkg_filter):
        ''' 
        get packages based on filter 
        @param pkg_filer: package list filter (Enum FILTER)
        @return: a list of packages
        '''
        raise NotImplementedError()

    def get_repositories(self):
        ''' 
        get repositories 
        @return: a list of repositories
        '''
        raise NotImplementedError()

    def enable_repository(self, repoid, enabled = True):
        ''' 
        set repository enable state
        @param repoid: repo id to change
        @param enabled: repo enable state
        '''
        raise NotImplementedError()

    def get_groups(self):
        ''' 
        get groups 
        @return: a list of groups
        '''
        raise NotImplementedError()

    def get_group_packages(self, group, grp_filter):
        ''' 
        get packages in a group 
        @param group: group id to get packages from
        @param grp_filter: group filters (Enum GROUP)
        '''
        raise NotImplementedError()

    def search(self, keys, sch_filters):
        ''' 
        get packages matching keys
        @param keys: list of keys to seach for
        @param sch_filters: list of search filter (Enum SEARCH)
        '''
        raise NotImplementedError()

class YumexPackageBase:
    '''
    This is an abstract package object for a package in the package system
   '''

    def __init__(self, pkg):
        self._pkg = pkg
        self.selected = False
        

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
    def repoid(self):
        return self._pkg.repoid

    @property
    def action(self):
        return self._pkg.action

    @property
    def summary(self):
        return self._pkg.summary

    @property
    def description(self):
        ''' Package description '''
        raise NotImplementedError()

    @property
    def changelog(self):
        ''' Package changelog '''
        raise NotImplementedError()

    @property
    def filelist(self):
        ''' Package filelist '''        
        raise NotImplementedError()

    @property        
    def id(self):
        ''' Return the package id '''        
        return '%s\t%s\t%s\t%s\t%s\t%s' % (self.name, self.epoch, self.version, self.release, self.arch, self.repoid)

    @property
    def filename(self):
        ''' Package id (the full package filename) '''        
        return "%s-%s.%s.%s.rpm" % (self.name, self.version, self.release, self.arch)

class YumexGroupBase:
    '''
    This is an abstract group object for a package in the package system
   '''

    def __init__(self, grp, category):
        self._grp = grp
        self._category = category
        self.selected = False

    @property
    def id(self):
        ''' Group id '''
        pass

    @property
    def name(self):
        ''' Group name '''
        pass

    @property
    def summary(self):
        ''' Group summary '''
        pass

    @property
    def description(self):
        ''' Group description '''
        pass
    
    @property
    def category(self):
        ''' Group category '''
        pass
    

class YumexTransactionBase:
    '''
    This is a abstract transaction queue for storing unprocessed changes
    to the system and to process the transaction on the system.
    '''
    def __init__(self, backend, frontend):
        '''
        initialize the transaction queue
        @param backend: The current YumexBackend
        @param frontend: the current YumexFrontend
        '''
        self.backend = backend
        self.frontend = frontend

    def add(self, po, action):
        '''
        add a package to the queue
        @param po: package to add to the queue
        '''
        pass

    def remove(self, po):
        '''
        remove a package from the queue
        @param po: package to remove from the queue
        '''
        pass

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

    def get_transaction_packages(self):
        '''
        Get the current packages in the transaction queue
        '''

