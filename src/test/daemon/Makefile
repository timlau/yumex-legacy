PKGDIR = /usr/share/yumex

all: 
	@../../../tools/py-compile *.py 

install:
	mkdir -p $(DESTDIR)/usr/share/dbus-1/system-services
	mkdir -p $(DESTDIR)/etc/dbus-1/system.d
	mkdir -p $(DESTDIR)/usr/share/polkit-1/actions
	mkdir -p $(DESTDIR)/usr/share/yumex		
	install -m644 dbus/org.yumex.service $(DESTDIR)/usr/share/dbus-1/system-services/.				
	install -m644 dbus/org.yumex.conf $(DESTDIR)/etc/dbus-1/system.d/.				
	install -m644 policykit1/org.yumex.policy $(DESTDIR)/usr/share/polkit-1/actions/.				
	install -m644 daemon.py $(DESTDIR)/$(PKGDIR)/.
	install -m644 daemon.pyc $(DESTDIR)/$(PKGDIR)/.
	install -m755 yumex-daemon $(DESTDIR)/$(PKGDIR)/.
	
refresh:
	@$(MAKE) all
	@sudo $(MAKE) install
	@sudo killall yumex-daemon
	
clean:
	@rm *.pyc *.pyo	

FORCE:
    