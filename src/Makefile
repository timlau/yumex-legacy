PKGDIR = /usr/share/yumex

clean:
	rm -fv *.pyc *.pyo *~ *.bak *.gladep
	rm -fv yumexgui/*.pyc yumexgui/*.pyo yumexgui/*~ 
	rm -fv yumexbase/*.pyc yumexbase/*.pyo yumexbase/*~ 
	rm -fv yumexbackend/*.pyc yumexbackend/*.pyo yumexbackend/*~ 

install:
	mkdir -p $(DESTDIR)/usr/share/yumex
	mkdir -p $(DESTDIR)/usr/bin
	install -m755 backend-launcher.* $(DESTDIR)/$(PKGDIR)/.
	install -m755 yum_childtask.* $(DESTDIR)/$(PKGDIR)/.
	install -m755 yumex.py $(DESTDIR)/usr/bin/yumex
	install -m644 *.glade $(DESTDIR)/$(PKGDIR)/.

pylint:
	@pylint --rcfile=test/yumex-pylintrc *.py yumexbase yumexgui yumexbackend guihelpers 2>/dev/null

pylint-short:
	@pylint -r n --rcfile=test/yumex-pylintrc *.py yumexbase yumexgui yumexbackend guihelpers 2>/dev/null

pylint-convertion:
	@pylint -r n --enable-msg-cat=C --rcfile=test/yumex-pylintrc *.py yumexbase yumexgui yumexbackend guihelpers 2>/dev/null
	
epydoc:
	@epydoc -o ../docs/epydoc --name "Yum Extender" --graph all yumexbase yumexbackend guihelpers yumexgui
