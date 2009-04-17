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

pylint:
	@pylint --rcfile=test/yumex-pylintrc *.py yumexbase