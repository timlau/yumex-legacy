#!/usr/bin/python

# playing with the yum history information

import yum

def get_name_dict(data):
    names = {}
    for hpo in data:
        if hpo.name in names:
            names[hpo.name].append(hpo)
        else:
            names[hpo.name] = [hpo]
    return names
    
def show_update(hpkgs):
    if hpkgs[0] > hpkgs[1]:
        new_pkg = hpkgs[0]
        old_pkg = hpkgs[1]
    else:
        new_pkg = hpkgs[1]
        old_pkg = hpkgs[0]
    if is_installed(new_pkg):
        print "   %s \n    --> + %s" % (old_pkg,new_pkg)
    else:
        print "   %s \n    -->   %s" % (old_pkg,new_pkg)


def is_installed(po):
    (n, a, e, v, r) = po.pkgtup
    po = yb.rpmdb.searchNevra(name=n, arch=a, ver=v, rel=r, epoch=e)
    if po:
        return po[0]
    else:
        return None   

yb = yum.YumBase()
ygh = yb.doPackageLists(pkgnarrow='installed')
hist=yb.history
tids=hist.old()
for i in xrange(0,5):
    tid = tids[i]
    print "Transaction : # ",tid.tid
    # show packages perfoming the transaction : rpm, yum, yumex etc
    print "with:"
    for hpo in tid.trans_with:
        print "  %s" % hpo
    # show packages included in the transaction
    print "Packages in Transaction"
    names = get_name_dict(tid.trans_data)
    for name in names:
        hpkgs = names[name]
        if len(hpkgs) > 1: # Must be an update 
            show_update(hpkgs)
        else:
            print name
            for hpo in names[name]:        
                if is_installed(hpo):
                    print " +(%s) : %s" % (hpo.state,hpo.pkgtup)
                else:
                    print "  (%s) : %s" % (hpo.state,hpo.pkgtup)
    # show skipped packages
    print "Skipped Packages in Transaction"
    for hpo in tid.trans_skip:
        print "  %s" % hpo
    # show errors
    print "Errors in transaction"
    for err in tid.errors:
        print err
    # show output 
    print "rpm output from transaction"
    for out in tid.output:
        print out
    print "Rpm problems"
    for err in tid.rpmdb_problems:
        print err

