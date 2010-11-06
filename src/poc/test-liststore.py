#!/usr/bin/python -tt

import gtk
import time
import gobject
import base64

class Dummy:

    def __init__(self):
        self.name = 'package'
        self.ver = '1.0'
        self.rel = '0.1.fc14'
        self.arch = 'x86_64'
        self.summary = "This is a packages"

def list_store(model, num=10):
    for i in xrange(num):
        print model[i][1]

def test_store1():
    print "Unsorted ListStore"
    start = time.time()
    d = Dummy()
    store = gtk.ListStore(gobject.TYPE_PYOBJECT, str, str, str, str, str, long)
    #store = gtk.ListStore(gobject.TYPE_PYOBJECT, str)
    for i in xrange(20000):
        store.append([d, "%s" % base64.b64encode(str(i)), "Some text", "Some text", "Some text", "Some text", 1000L])
        #store.append([d, d.name])
    end = time.time()
    print ("test_store1 time : %.2f " % (end - start))
    list_store(store)

def test_store2():
    print "TreeModelSort (set_sort_column_id(1, gtk.SORT_ASCENDING) before population)"
    start = time.time()
    d = Dummy()
    store = gtk.ListStore(gobject.TYPE_PYOBJECT, str, str, str, str, str, long)
    sort_store = gtk.TreeModelSort(store)
    sort_store.set_sort_column_id(1, gtk.SORT_ASCENDING)
    for i in xrange(20000):
        store.append([d, "%s" % base64.b64encode(str(i)), "Some text", "Some text", "Some text", "Some text", 1000L])
    end = time.time()
    print ("test_store2 time : %.2f " % (end - start))
    list_store(sort_store)

def test_store3():
    print "TreeModelSort (set_sort_column_id(1, gtk.SORT_ASCENDING) after population)"
    start = time.time()
    d = Dummy()
    store = gtk.ListStore(gobject.TYPE_PYOBJECT, str, str, str, str, str, long)
    sort_store = gtk.TreeModelSort(store)
    #sort_store.set_default_sort_func(lambda *args: -1) 
    for i in xrange(20000):
        store.append([d, "%s" % base64.b64encode(str(i)), "Some text", "Some text", "Some text", "Some text", 1000L])
    sort_store.set_sort_column_id(1, gtk.SORT_ASCENDING)
    end = time.time()
    print ("test_store3 time : %.2f " % (end - start))
    list_store(sort_store)

def test_store4():
    start = time.time()
    d = Dummy()
    store = gtk.ListStore(gobject.TYPE_PYOBJECT, str, str, str, str, str, long)
    sort_store = gtk.TreeModelSort(store)
    #sort_store.set_default_sort_func(lambda *args: -1) 
    sort_store.set_sort_column_id(-1, gtk.SORT_ASCENDING)
    for i in xrange(20000):
        store.append([d, "%s" % base64.b64encode(str(i)), "Some text", "Some text", "Some text", "Some text", 1000L])
    sort_store.set_sort_column_id(1, gtk.SORT_ASCENDING)
    end = time.time()
    print ("test_store4 time : %.2f " % (end - start))
    list_store(sort_store)


if __name__ == "__main__":
    test_store1()
    test_store2()
    test_store3()
    test_store4()
