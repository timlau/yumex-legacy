


class YumexBackendBase(object):
    '''
    Yumex Backend Base class
    This is the base class to interact with the package system    
    '''
    def __init__(self,frontend,transaction):
        ''' 
        init the backend 
        @param frontend: the current frontend
        '''
        self.frontend = frontend
        self.transaction = transaction

    def setup(self):
        ''' Setup the backend'''
        pass

    def reset(self):
        ''' Reset the backend, so it can be setup again'''
        pass

    def get_packages(self, pkg_filter):
        ''' 
        get packages based on filter 
        @param pkg_filer: package list filter (Enum FILTER)
        @return: a list of packages
        '''
        pass

    def get_repositories(self):
        ''' 
        get repositories 
        @return: a list of repositories
        '''
        pass

    def enable_repository(self, repoid, enabled=True):
        ''' 
        set repository enable state
        @param repoid: repo id to change
        @param enabled: repo enable state
        '''
        pass

    def get_groups(self):
        ''' 
        get groups 
        @return: a list of groups
        '''
        pass

    def get_group_packages(self, group, grp_filter):
        ''' 
        get packages in a group 
        @param group: group id to get packages from
        @param grp_filter: group filters (Enum GROUP)
        '''
        pass

    def search(self, keys, sch_filters):
        ''' 
        get packages matching keys
        @param keys: list of keys to seach for
        @param sch_filters: list of search filter (Enum SEARCH)
        '''
        pass

class YumexPackageBase:
    '''
    This is an abstract package object for a package in the package system
   '''

    def __init__(self, pkg):
        self._pkg = pkg
        self.selected = False
        

    @property
    def name(self):
        ''' Package name '''
        pass

    @property
    def version(self):
        ''' Package version '''
        pass

    @property
    def release(self):
        ''' Package release '''
        pass

    @property
    def arch(self):
        ''' Package architecture '''
        pass

    @property
    def repoid(self):
        ''' Package repoid '''
        pass

    @property
    def action(self):
        ''' Package tsInfo State '''
        pass

    @property
    def summary(self):
        ''' Package summary '''
        pass

    @property
    def description(self):
        ''' Package description '''
        pass

    @property
    def changelog(self):
        ''' Package changelog '''
        pass

    @property
    def filelist(self):
        ''' Package filelist '''        
        pass

    @property
    def id(self):
        ''' Package id (the full packagename) '''        
        return "%s-%s.%s.%s" % (self.name, self.version, self.release, self.arch)

    @property
    def filename(self):
        ''' Package id (the full package filename) '''        
        return "%s-%s.%s.%s.rpm" % (self.name, self.version, self.release, self.arch)

class YumexGroupBase:
    '''
    This is an abstract group object for a package in the package system
   '''

    def __init__(self, grp,category):
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
        self._backend = backend
        self._frontend = frontend

    def add(self, po):
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

class YumexProgressElememt:
    '''
    This class stores the progress values for a single element
    '''

    def __init__(self, name, size):
        ''' init the current element '''
        self.name = name
        self.size = size
        self.downloaded = 0L
        self.eta = 0L
        self.speed = 0L

    def reset(self):
        ''' reset the progress '''
        self.downloaded = 0L
        self.ETA = 0L
        self.speed = 0L

    def set_progress(self,downloaded, eta, speed):
        ''' set progress for current element'''
        self.downloaded = downloaded
        self.eta = eta
        self.speed = speed

class YumexProgressBase:
    '''
    This is a actract progress class to store the current progress
    '''

    def __init__(self):
        ''' init the progress '''
        self._names = {}
        self._current = None

    def set_packages(self, pkgs):
        ''' set the packages to work on'''
        self._names = {}
        for pkg in pkgs:
            self._names[pkg.name] = pkg

    def set_current(self, current):
        ''' Set the current element '''
        self._current = current

    def get_current(self):
        ''' get the current element '''
        return self._current


