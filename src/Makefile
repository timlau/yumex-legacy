PKGDIR = /usr/share/yumex

all: 
	@../tools/py-compile *.py 

clean:
	rm -fv *.pyc *.pyo *~ *.bak *.gladep
	rm -fv yumexgui/*.pyc yumexgui/*.pyo yumexgui/*~ 
	rm -fv yumexbase/*.pyc yumexbase/*.pyo yumexbase/*~ 
	rm -fv yumexbackend/*.pyc yumexbackend/*.pyo yumexbackend/*~ 

install:
	mkdir -p $(DESTDIR)/usr/share/yumex
	mkdir -p $(DESTDIR)/usr/share/yumex
	install -m755 *.pyc $(DESTDIR)/$(PKGDIR)/.
	install -m755 *.py $(DESTDIR)/$(PKGDIR)/.
	install -m644 yumex.glade $(DESTDIR)/$(PKGDIR)/.
	chmod +x $(DESTDIR)/$(PKGDIR)/yum_childtask.py
	ln -s  $(DESTDIR)/$(PKGDIR)/yum_childtask.py $(DESTDIR)/$(PKGDIR)/yumex-yum-backend

pylint:
	@pylint --rcfile=test/yumex-pylintrc *.py yumexbase yumexgui yumexbackend guihelpers 2>/dev/null

pylint-short:
	@pylint -r n --rcfile=test/yumex-pylintrc *.py yumexbase yumexgui yumexbackend guihelpers 2>/dev/null

pylint-convertion:
	@pylint -r n --enable-msg-cat=C --rcfile=test/yumex-pylintrc *.py yumexbase yumexgui yumexbackend guihelpers 2>/dev/null
	
epydoc:
	@epydoc -o ../docs/epydoc --name "Yum Extender" --graph all yumexbase yumexbackend guihelpers yumexgui