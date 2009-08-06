%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:     yumex
Version:  2.9.0
Release:  0.9.pre%{?dist}
Summary:  Yum Extender graphical package management tool

Group:    Applications/System
License:  GPLv2+
URL:      http://www.yum-extender.org
Source0:  http://www.yum-extender.org/dnl/yumex/source/%{name}-%{version}.tar.gz
BuildRoot:%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch: noarch
BuildRequires: python-devel
BuildRequires: desktop-file-utils
BuildRequires: gettext
BuildRequires: intltool


Requires: yum >= 3.2.21
Requires: pygtk2 >= 2.14
Requires: usermode
Requires: pexpect
Requires: python-enum
Requires: python-iniparse

%description
Graphical User Interface for Yum.


%prep
%setup -q


%build
make


%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install

desktop-file-install --vendor fedora --delete-original \
    --dir $RPM_BUILD_ROOT%{_datadir}/applications \
    --add-category X-Fedora \
    $RPM_BUILD_ROOT%{_datadir}/applications/%{name}.desktop

# this is a doc file; removing from installed tree
rm $RPM_BUILD_ROOT%{_datadir}/yumex/COPYING

%find_lang %name


%clean
rm -rf $RPM_BUILD_ROOT

%files -f  %{name}.lang
%defattr(-, root, root, -)
%doc COPYING ChangeLog TODO
%{_datadir}/pixmaps/yumex
%{_datadir}/yumex
%{_bindir}/yumex*
%{python_sitelib}/yumexbackend/
%{python_sitelib}/yumexbase/
%{python_sitelib}/yumexgui/
%{python_sitelib}/guihelpers/
%config(noreplace)  %{_sysconfdir}/yumex.profiles.conf
%config(noreplace)  %{_sysconfdir}/yumex.conf
%config %{_sysconfdir}/pam.d/yumex-yum-backend
%config %{_sysconfdir}/security/console.apps/-yum-backend

%{_datadir}/applications/fedora-%{name}.desktop

%changelog
* Sun May 24 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.9.pre
- bumped version to 2.9.0-0.9.pre
- handle new yumex-yum-backend in %%files section 
* Sun May 24 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.8.pre
- bumped version to 2.9.0-0.8.pre
* Wed May 20 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.7.pre
- bumped version to 2.9.0-0.7.pre
* Sun May 10 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.6.pre
- bumped version to 2.9.0-0.6.pre
* Wed May 6 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.5.pre
- bumped version to 2.9.0-0.5.pre
* Thu Apr 30 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.4.pre
- bumped version to 2.9.0-0.4.pre
- added minimum version for pygtk requirement
* Sat Apr 25 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.3.pre
- bumped version to 2.9.0-0.3.pre
* Tue Apr 21 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.2.pre
- bumped version to 2.9.0-0.2.pre
* Tue Apr 21 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.1.pre
- bumped version to 2.9.0-0.1.pre
* Tue Apr 21 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.1.0-0.2.pre
- Added guihelpers to %%files
* Fri Oct 24 2008 Tim Lauridsen <timlau@fedoraproject.org> - 2.1.0-0.1.pre
- bumped version to 2.1.0-0.1.pre
- added pexpect & python-enum requires.
- added yumex* python modules to %%files
* Thu Feb 21 2008 Tim Lauridsen <tla@rasmil.dk> - 2.0.4-1
- Release 2.0.4
* Mon Nov 19 2007 Tim Lauridsen <tla@rasmil.dk> - 2.0.3-2
- fixed missing '\\n' in fr.po
* Mon Nov 19 2007 Tim Lauridsen <tla@rasmil.dk> - 2.0.3-1
- Release 2.0.3
* Fri Sep 28 2007 Tim Lauridsen <tla@rasmil.dk> - 2.0.2-1
- Release 2.0.2
* Wed Aug 22 2007 Tim Lauridsen <tla@rasmil.dk> - 2.0.1-1
- Release 2.0.1
* Thu Aug 16 2007 Tim Lauridsen <tla@rasmil.dk> - 2.0-1
- Release 2.0 GA
- Updated license tag to apply to Fedora guidelines.
* Sun Jul 8 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.11-1
- Development Release 1.9.11-1
* Sun Jul 8 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.10-2.0
- Development Release 1.9.10-2.0
* Sat Jul 7 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.10-1.0
- Development Release 1.9.10-1.0
* Tue Jun 12 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.9-1.0
- Development Release 1.9.9-1.0
* Mon Jun 4 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.8-2.0
- Development Release 1.9.8-2.0
- Forgot to update changelog
* Mon Jun 4 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.8-1.0
- Development Release 1.9.8-1.0
* Tue May 29 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.7-1.0
- Development Release 1.9.7-1.0
* Tue Apr 17 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.6-1.0
- Development Release 1.9.6-1.0
* Mon Mar 20 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.5-1.0
- Development Release 1.9.5-1.0
* Mon Mar 19 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.4-1.0
- Development Release 1.9.4-1.0
* Fri Feb 16 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.3-1.0
- Development Release 1.9.3-1.0
* Tue Jan 30 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.2-1.1
- Development Release 1.9.2-1.1
* Mon Jan 29 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.2-1.0
- Development Release 1.9.2-1.0
* Mon Jan 8 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.2-0.1.pre1
- Development Release 1.9.2-0.1.pre1
* Sun Jan 7 2007 Tim Lauridsen <tla@rasmil.dk> - 1.9.1-1.0
- Development Release 1.9.1-1.0
* Fri Dec 22 2006 Tim Lauridsen <tla@rasmil.dk> - 1.9.1-0.1.pre1
- Development Release 1.9.1-0.1.pre1
* Fri Dec 22 2006 Tim Lauridsen <tla@rasmil.dk> - 1.9.0-1.2
- Updated SOURCE url to the right place
- fixed rpmlint errors: macros in changelog.
* Wed Dec 18 2006 Tim Lauridsen <tla@rasmil.dk> - 1.9.0-1.1
- Updated urls to new yumex homepage
- using %%{python_sitearch} macro insted of hardcode path
* Wed Dec 18 2006 Tim Lauridsen <tla@rasmil.dk> - 1.9.0-1.0
- Development Release 1.9.0-1.0
* Wed Nov 22 2006 Tim Lauridsen <tla@rasmil.dk> - 1.9.0-0.1.pre2
- Development Release 1.9.0-0.1.pre2
* Wed Oct 25 2006 Tim Lauridsen <tla@rasmil.dk> - 1.9.0-0.1.pre1
- Development Release 1.9.0-0.1.pre1
* Wed Oct 25 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.7-1.0
- Development Release 1.1.7-1.0
* Wed Oct 25 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.6-1.0
- Development Release 1.1.6-1.0
* Sun Oct 22 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.5-2.0
- bumped release for new build
* Sun Oct 22 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.5-1.0
- Development Release 1.1.5-1.0
* Mon Oct 9 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.4-2.0
- Development Release 1.1.4-2.0
- Updated Requires: yum >= 3.0.0 to yum >= 3.0
* Sat Oct 7 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.4-1.0
- Development Release 1.1.4-1.0
- Updated Requires: yum >= 2.9.6 to yum >= 3.0.0
* Wed Sep 6 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.3-1.0
- Development Release 1.1.3-1.0
- Updated Requires: yum >= 2.9.5 to yum >= 2.9.6
* Fri Aug 25 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.2-1.0
- Development Release 1.1.2-1.0
- Updated Requires: yum >= 2.9.3 to yum >= 2.9.5
* Thu Aug 17 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.1-1.0
- Development Release 1.1.1-1.0
* Wed Aug 16 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.1-0.3.pre3
- Development Release 1.1.1-0.3.pre3
* Fri Aug 11 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.1-0.2.pre2
- Development Release 1.1.1-0.2.pre2
* Thu Aug 10 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.1-0.1.pre1
- Development Release 1.1.1-0.1.pre1
- Updated yum >= 2.9 to yum >= 2.9.3 
* Mon Jun 19 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.0-2.0
- BuildRequires: intltool
* Wed May 3 2006 Tim Lauridsen <tla@rasmil.dk> - 1.1.0-1.0
- Development Release 1.1.0-1.0
- Requires: yum >= 2.9 (Because of yum API Changes)
* Fri Apr 21 2006 Tim Lauridsen <tla@rasmil.dk> - 1.0.0-1.0
- Release 1.0.0-1.0
* Fri Apr 21 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.17-1.0
- Development Release 0.99.17-1.0
* Thu Mar 30 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.16-1.0
- Development Release 0.99.16-1.0
* Wed Mar 22 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.15-1.0
- Development Release 0.99.15-1.0
* Mon Mar 20 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.14-1.0
- Development Release 0.99.14-1.0
* Mon Mar 13 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.13-1.0
- Development Release 0.99.13-1.0
* Mon Mar 13 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.12-1.0
- Development Release 0.99.12-1.0
- Added '-q' option to %%setup
* Tue Feb 28 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.11-1.0
- Development Release 0.99.11-1.0
* Tue Feb 15 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.10-1.0
- Development Release 0.99.10-1.0
* Tue Feb 14 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.9-1.0
- Development Release 0.99.9-1.0
* Tue Feb 14 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.8-1.0
- Development Release 0.99.8-1.0
* Thu Feb 09 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.7-1.0
- Development Release 0.99.7-1.0
* Thu Feb 09 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.6-2.0
- Development Release 0.99.6-2.0
- Requires: yum  from 2.5 to 2.4
* Thu Feb 09 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.5-1.0
- Development Release 0.99.5-1.0
* Sun Feb 05 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.4-1.0
- Development Release 0.99.4-1.0
* Thu Jan 26 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.3-1.0
- Development Release 0.99.3-1.0
* Wed Jan 25 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.2-1.0
- Development Release 0.99.2-1.0
* Tue Jan 24 2006 Tim Lauridsen <tla@rasmil.dk> - 0.99.1-1.0
- Development Release 0.99.1-1.0
- Changed versioning from X.Y to X.Y.Z
- Remove build_v
- Removed build_v from source0
- Added /usr/lib/python?.?/site-packages/yumex to %%files
- Added /usr/lib/python?.?/site-packages/yumgui to %%files
* Fri Jan 6 2006 Tim Lauridsen <tla@rasmil.dk> - 0.45-2.0
- Development Release 0.45-2.0
- Lot of changes, check the changelog.
* Tue Dec 20 2005 Tim Lauridsen <tla@rasmil.dk> - 0.45-1.0
- Development Release 0.45-1.0
- Changed to work with yum 2.5.0
- Requires: yum >= 2.5
- Same features as 0.44-1.0, but uses yum 2.5.0 API 
* Thu Dec 15 2005 Tim Lauridsen <tla@rasmil.dk> - 0.44-1.0
- Public Release 0.44-1.0
* Sun Dec 11 2005 Tim Lauridsen <tla@rasmil.dk> - 0.43-10.0
- Release 0.43-10.0
* Sat Dec 10 2005 Tim Lauridsen <tla@rasmil.dk> - 0.43-9.0
- Release 0.43-9.0
* Wed Nov 23 2005 Tim Lauridsen <tla@rasmil.dk> - 0.43-8.0
- Release 0.43-8.0
* Wed Nov 23 2005 Tim Lauridsen <tla@rasmil.dk> - 0.43-7.0
- Release 0.43-7.0
* Fri Nov 18 2005 Tim Lauridsen <tla@rasmil.dk> - 0.43-6.0
- Release 0.43-6.0
* Thu Nov 17 2005 Tim Lauridsen <tla@rasmil.dk> - 0.43-5.0
- Release 0.43-5.0
* Wed Nov 16 2005 Tim Lauridsen <tla@rasmil.dk> - 0.43-4.0
- Release 0.43-4.0
* Thu Nov 8 2005 Tim Lauridsen <tla@rasmil.dk> - 0.43-3.0
- Release 0.43-3.0
* Thu Nov 7 2005 Tim Lauridsen <tla@rasmil.dk> - 0.43-2.0
- Release 0.43-2.0
* Thu Nov 7 2005 Tim Lauridsen <tla@rasmil.dk> - 0.43-1.0
- Release 0.43-1.0
- Lot of changes, check the ChangeLog
* Thu Oct 13 2005 Tim Lauridsen <tla@rasmil.dk> - 0.42-8.0
- Release 0.42-8.0
* Thu Oct 13 2005 Tim Lauridsen <tla@rasmil.dk> - 0.42-7.0
- Release 0.42-7.0
- Changed Requires: yum to >= 2.4
- Fixed exclude list, now it works again.
- Add a Gnome HIG compliance patches (Thanks to Dennis Cranston)
- Fixed bug when creating new repos on repo page.
- Added new icon (Thanks to Dennis Cranston)
* Thu Oct 6 2005 Tim Lauridsen <tla@rasmil.dk> - 0.42-6.0
- Release 0.42-6.0
- added MATSUURA Takanori's menu keyboard navigation patch 
- added Japanese translation (Thanks to MATSUURA Takanori)
- disabled yum plugins in yumex. (Bugzilla #168595)
- fixed wrong space chars in french translation (Bugzilla #167881)
* Sat Sep 3 2005 Tim Lauridsen <tla@rasmil.dk> - 0.42-5.0
- Release 0.42-5.0
* Tue Aug 30 2005 Tim Lauridsen <tla@rasmil.dk> - 0.42-4.0
- Release 0.42-4.0
- Fixed delete repo on repos page. (Rightclick + Delete now working)
- Fixed UTF-8 bugs, when strings are encoded with iso-8859-1.
* Sat Aug 20 2005 Tim Lauridsen <tla@rasmil.dk> - 0.42-3.0
- Release 0.42-3.0
- Fixed Dependencies not resolved bug.
* Wed Aug 17 2005 Tim Lauridsen <tla@rasmil.dk> - 0.42-2.0
- Release 0.42-2.0
- Fixed TypeError in yumexBase.errorlog in yumbase.py


* Wed Aug 17 2005 Tim Lauridsen <tla@rasmil.dk> - 0.42-1.0
- Release 0.42
- Added Requires: pygtk2-libglade (Bugzilla 163439)
- A lot of changes and new features, check Changelog for details.
* Tue Jun 21 2005 Michael A. Peters <mpeters@mac.com> - 0.40-5.1
- removed unnecessary [ "$RPM_BUILD_ROOT" != "/" ] checks
- commented out python-abi check - automatic in fc4
- added gettext BuildRequires
- removed --add-category X-Red-Hat-Base

* Mon Jun 20 2005 Tim Lauridsen <tla@rasmil.dk> 0.40-4.2
- updated build_v to 4.2 & release to 4.2, They have to match
* Mon Jun 20 2005 Michael A. Peters <mpeters@mac.com> - 0.40-4.1
- added build_v macro
- change {release} in Source0 to %%{build_v} so it would properly expand when
- {?dist} is defined

* Mon Jun 20 2005 Tim Lauridsen <tla@rasmil.dk> 0.40-4
- Add Release to source tar.gz
- Changed Source0 URL
- Fixed absolut link in Makefile (consolehelper)
- Updated Release in yumex.py
- Update archive section in Makefile to include release in tar.gz.
* Sun Jun 19 2005 Tim Lauridsen <tla@rasmil.dk> 0.40-3
- Moved yumex.profiles.conf back to /etc.
- Added Fedora repos to yumex.repos.conf.
- Added full URL to Source0.
- Added Requires: usermode.
- Fixed files section.

* Sat Jun 18 2005 Tim Lauridsen <tla@rasmil.dk>
- added yumex.repos.conf again, it is used at a template for creating .repo files by
  the yumex repo installer, it is not used at a yum.conf replacement.
- moved yumex.profiles.conf & yumex.repos.conf from /etc to /usr/share/yumex.
- clean out the yumex.repos.conf, because it contains links to grayzone stuff.
* Fri Jun 17 2005 Matthew Miller <mattdm@mattdm.org> - 0.40-2
- clean up formatting of rpm header lines to match typical FE packages
- remove some rpm-howto/template comments
- don't need to go deleting the buildroot quite so often
- put some whitespace in the changelog to stop my eyes from bleeding ;)
- move to group Applications/System to match system-config-packages
- find_lang instead of listing datadir/locale in files
- buildrequires python-devel, not just plain python
- requires python-abi magicstuff
- remove echo statements from post scriptlet -- rpm should be quiet 
  except in emergencies
- actually, remove that entirely -- instead, put the default config file
  in place as config(noreplace)
- add ChangeLog as doc file
- remove COPYING from the installed tree; add as doc file
- list more files explicitly instead of using wildcards -- more work, but
  safer
- install .desktop file with desktop-file-install
- default permissions are right for .desktop file -- not listing separately
- add symlink for consolehelper
- remove yumex.repos.conf -- use regular /etc/yum.repos.d repos instead
  (and, the default ones contain several not-safe-for-fedora repos)

* Wed Jun 15 2005 Tim Lauridsen <tla@rasmil.dk>
- 0.40-01 FC4 release Build

* Mon May 17 2005 Tim Lauridsen <tla@rasmil.dk>
- 0.39-03 FC4 prerelease Build

* Thu May 13 2005 Tim Lauridsen <tla@rasmil.dk>
- 0.39-02 FC4 prerelease Build

* Thu Apr 28 2005 Tim Lauridsen <tla@rasmil.dk>
- 0.39-01 First FC4 prerelease Build

* Mon Apr 11 2005 Tim Lauridsen <tla@rasmil.dk>
- 0.34-01 Release Build

* Wed Apr 06 2005 Tim Lauridsen <tla@rasmil.dk>
- 0.33-03

* Thu Mar 31 2005 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.33-02
- No Requires : yum >= 2.2.0
- Removed gpgkey installation, yum 2.2.0 can handle this

* Tue Mar 29 2005 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.33-01
- Now using make to do the real stuff.

* Fri Mar 4 2005 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.32-5
- Changed post install to only install i yumex.conf if it not exists.

* Wed Mar 2 2005 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.32-2

* Thu Feb 24 2005 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.32-1

* Fri Feb 11 2005 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.31-1
- Release 0.31

* Tue Jan 25 2005 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.30-2
- fixed error printing emtpy string (yum info package) 

* Tue Jan 25 2005 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.30-1 
- Added GPL License (COPYING) to package
- Added automatic refresh at program start.

* Sat Jan 22 2005 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.30 Build

* Wed Dec 22 2004 Tim Lauridsen <tla@rasmil.dk>
- fixed problem with no repos in yum.conf

* Mon Dec 20 2004 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.23 RPM Build

* Sun Dec 19 2004 Tim Lauridsen <tla@rasmil.dk>
- Changed permission flags on non execution files (755 -> 644)

* Tue Dec 13 2004 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.22 RPM Build

* Tue Dec 7 2004 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.21 RPM Build

* Tue Nov 30 2004 Tim Lauridsen <tla@rasmil.dk>
- Ver 0.20 RPM Build

* Wed Nov 24 2004 Tim Lauridsen <tla@rasmil.dk>
- Initial RPM Build
