#!/usr/bin/python -tt

import gtk
import time
import gobject

class Dummy:

    def __init__(self):
        self.name = 'package'
        self.ver = '1.0'
        self.rel = '0.1.fc14'
        self.arch = 'x86_64'
        self.summary = "This is a packages"


def test_store1():
    start = time.time()
    dummy = Dummy()
    store = gtk.ListStore(gobject.TYPE_PYOBJECT, str)
    for i in xrange(20000):
        store.append([dummy, dummy.name])
    end = time.time()
    print ("test_store1 time : %.2f " % (end - start))

def test_store2():
    start = time.time()
    d = Dummy()
    #store = gtk.ListStore(gobject.TYPE_PYOBJECT, str, str, str, str, str, long)
    store = gtk.ListStore(gobject.TYPE_PYOBJECT, str, str, str, str, long)
    sort_store = gtk.TreeModelSort(store)
    for i in xrange(20000):
        #store.append([d, "Some text", "Some text", "Some text", "Some text", "Some text", 1000L])
        store.append([d, "Some text", "Some text", "Some text", "Some text",  1000L])
    end = time.time()
    print ("test_store2 time : %.2f " % (end - start))

if __name__ == "__main__":
    test_store1()
    test_store2()