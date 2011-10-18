SUBDIRS = src po src/yumexbase src/yumexgui src/yumexbackend src/guihelpers
PYFILES = $(wildcard *.py)
PKGNAME = yumex
VERSION=$(shell awk '/Version:/ { print $$2 }' ${PKGNAME}.spec)
PYTHON=python
SRCDIR=src
MISCDIR=misc
PIXDIR=gfx
ALLDIRS=$(SUBDIRS) gfx misc tools
GITDATE=git$(shell date +%Y%m%d)
VER_REGEX=\(^Version:\s*[0-9]*\.[0-9]*\.\)\(.*\)
BUMPED_MINOR=${shell VN=`cat ${PKGNAME}.spec | grep Version| sed  's/${VER_REGEX}/\2/'`; echo $$(($$VN + 1))}
NEW_VER=${shell cat ${PKGNAME}.spec | grep Version| sed  's/\(^Version:\s*\)\([0-9]*\.[0-9]*\.\)\(.*\)/\2${BUMPED_MINOR}/'}
NEW_REL=0.1.${GITDATE}
all: subdirs
	
subdirs:
	for d in $(SUBDIRS); do make -C $$d; [ $$? = 0 ] || exit 1 ; done

clean:
	@rm -fv *~ *.tar.gz *.list *.lang 
	for d in $(SUBDIRS); do make -C $$d clean ; done

install:
	mkdir -p $(DESTDIR)/usr/share/yumex
	mkdir -p $(DESTDIR)/usr/share/pixmaps/yumex
	mkdir -p $(DESTDIR)/usr/share/applications
	mkdir -p $(DESTDIR)/usr/bin
	mkdir -p $(DESTDIR)/etc
	mkdir -p $(DESTDIR)/etc/pam.d
	mkdir -p $(DESTDIR)/etc/security/console.apps
	install -m644 COPYING $(DESTDIR)/usr/share/yumex/.
	install -m755 $(MISCDIR)/yumex $(DESTDIR)/usr/bin/yumex
	install -m644 $(PIXDIR)/*.png $(DESTDIR)/usr/share/pixmaps/yumex/.
	install -m644 $(PIXDIR)/*.gif $(DESTDIR)/usr/share/pixmaps/yumex/.
	install -m644 $(MISCDIR)/yumex.profiles.conf $(DESTDIR)/etc/.
	install -m644 $(MISCDIR)/yumex-yum-backend.pam $(DESTDIR)/etc/pam.d/yumex-yum-backend
	install -m644 $(MISCDIR)/yumex.conf.default $(DESTDIR)/etc/yumex.conf
	install -m644 $(MISCDIR)/yumex-yum-backend.console.app $(DESTDIR)/etc/security/console.apps/yumex-yum-backend
	ln -s consolehelper $(DESTDIR)/usr/bin/yumex-yum-backend
	install -m644 $(MISCDIR)/yumex.desktop $(DESTDIR)/usr/share/applications/.
	for d in $(SUBDIRS); do make DESTDIR=`cd $(DESTDIR); pwd` -C $$d install; [ $$? = 0 ] || exit 1; done

get-builddeps:
	yum install perl-TimeDate python-devel gettext intltool rpmdevtools

archive:
	@rm -rf ${PKGNAME}-${VERSION}.tar.gz
	@git archive --format=tar --prefix=$(PKGNAME)-$(VERSION)/ HEAD | gzip -9v >${PKGNAME}-$(VERSION).tar.gz
	@cp ${PKGNAME}-$(VERSION).tar.gz $(shell rpm -E '%_sourcedir')
	@rm -rf ${PKGNAME}-${VERSION}.tar.gz
	@echo "The archive is in ${PKGNAME}-$(VERSION).tar.gz"
	
# needs perl-TimeDate for git2cl
changelog:
	@git log --pretty --numstat --summary --after=2008-10-22 | tools/git2cl > ChangeLog
	
upload: FORCE
	@scp ~/rpmbuild/SOURCES/${PKGNAME}-${VERSION}.tar.gz yum-extender.org:public_html/dnl/yumex/source/.
    
release:
	@git commit -a -m "bumped version to $(VERSION)"
	@$(MAKE) changelog
	@git commit -a -m "updated ChangeLog"
	@git push
	@git tag -f -m "Added ${PKGNAME}-${VERSION} release tag" ${PKGNAME}-${VERSION}
	@git push --tags origin
	@$(MAKE) archive
	@$(MAKE) upload

test-cleanup:	
	@rm -rf ${PKGNAME}-${VERSION}.test.tar.gz
	@echo "Cleanup the git release-test local branch"
	@git checkout -f
	@git checkout master
	@git branch -D release-test

show-vars:
	@echo ${GITDATE}
	@echo ${BUMPED_MINOR}
	@echo ${NEW_VER}-${NEW_REL}
	
test-release:
	@git checkout -b release-test
	# +1 Minor version and add 0.1-gitYYYYMMDD release
	@cat ${PKGNAME}.spec | sed  -e 's/${VER_REGEX}/\1${BUMPED_MINOR}/' -e 's/\(^Release:\s*\)\([0-9]*\)\(.*\)./\10.1.${GITDATE}%{?dist}/' > ${PKGNAME}-test.spec ; mv ${PKGNAME}-test.spec ${PKGNAME}.spec
	@git commit -a -m "bumped ${PKGNAME} version ${NEW_VER}-${NEW_REL}"
	# Make Changelog
	@git log --pretty --numstat --summary | ./tools/git2cl > ChangeLog
	@git commit -a -m "updated ChangeLog"
    	# Make archive
	@rm -rf ${PKGNAME}-${NEW_VER}.tar.gz
	@git archive --format=tar --prefix=$(PKGNAME)-$(NEW_VER)/ HEAD | gzip -9v >${PKGNAME}-$(NEW_VER).tar.gz
	# Build RPMS
	@rpmdev-wipetree
	@rpmbuild -ta ${PKGNAME}-${NEW_VER}.tar.gz
	@$(MAKE) test-cleanup
	
rpm:
	@$(MAKE) archive
	@rpmbuild -ba yumex.spec
	
test-builds:
	@$(MAKE) test-release
	@ssh timlau.fedorapeople.org rm public_html/files/yumex/*
	@scp ${PKGNAME}-${NEW_VER}.tar.gz timlau.fedorapeople.org:public_html/files/yumex/${PKGNAME}-${NEW_VER}-${GITDATE}.tar.gz
	@scp ~/rpmbuild/RPMS/noarch/${PKGNAME}-${NEW_VER}*.rpm timlau.fedorapeople.org:public_html/files/yumex/.
	@scp ~/rpmbuild/SRPMS/${PKGNAME}-${NEW_VER}*.rpm timlau.fedorapeople.org:public_html/files/yumex/.


transifex-pull:
      tx pull -a -f
      @echo "You can now git commit -a -m 'Transfix pull, *.po update'"

transifex-push:
      make -C po yumex.pot
      tx push -s -t
      @echo "You can now git commit -a -m 'Transfix push, yum.pot update'"
		
FORCE:
    
