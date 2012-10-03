%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:     yumex
Version:  3.0.8
Release:  1%{?dist}
Summary:  Yum Extender graphical package management tool

Group:    Applications/System
License:  GPLv2+
URL:      http://www.yumex.dk
Source0:  https://fedorahosted.org/releases/y/u/yumex/%{name}-%{version}.tar.gz
BuildRoot:%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch: noarch
BuildRequires: python-devel
BuildRequires: desktop-file-utils
BuildRequires: gettext
BuildRequires: intltool


Requires: yum >= 3.2.23
Requires: pygtk2 >= 2.14
Requires: pexpect
Requires: python-iniparse
Requires: dbus-python
Requires: udisks
Requires: python-kitchen
Requires: urlgrabber
Requires: polkit
Requires: pyxdg

%description
Graphical User Interface for Yum.


%prep
%setup -q


%build
make


%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install

#install another .glade file for el6
%if 0%{?el6}
install -m644 src/yumex.glade.el6 $RPM_BUILD_ROOT/%{_datadir}/%{name}/yumex.glade
%endif

desktop-file-install --vendor fedora --delete-original \
    --dir $RPM_BUILD_ROOT%{_datadir}/applications \
    --add-category X-Fedora \
    $RPM_BUILD_ROOT%{_datadir}/applications/%{name}.desktop

desktop-file-install --vendor fedora --delete-original \
    --dir $RPM_BUILD_ROOT%{_datadir}/applications \
    --add-category X-Fedora \
    $RPM_BUILD_ROOT%{_datadir}/applications/%{name}-local.desktop
    
# this is a doc file; removing from installed tree
rm $RPM_BUILD_ROOT%{_datadir}/yumex/COPYING

%find_lang %name

%post
update-desktop-database %{_datadir}/applications &> /dev/null || :

%postun
update-desktop-database %{_datadir}/applications &> /dev/null || :

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
%{_datadir}/polkit-1/actions/dk.yumex.backend.policy
%{_datadir}/applications/*.desktop

%changelog
* Wed Oct 3 2012 Tim Lauridsen <timlau@fedoraproject.org> 3.0.8-1
- bumped version to 3.0.8-1
* Thu Sep 13 2012 Tim Lauridsen <timlau@fedoraproject.org> 3.0.7-2
- Install another .desktop file with mimetype for local .rpm install
- update desktop database post install & post uninstall
* Wed Sep 12 2012 Tim Lauridsen <timlau@fedoraproject.org> 3.0.7-1
- bumped version to 3.0.7-1
* Fri Sep 07 2012 Tim Lauridsen <timlau@fedoraproject.org> 3.0.6-2
- renamed polkit policy to dk.yumex.backend.policy
* Wed Aug 08 2012 Tim Lauridsen <timlau@fedoraproject.org> 3.0.6-1
- bumped version to 3.0.6-1
- Changed project url & source url
* Tue May 15 2012 Tim Lauridsen <timlau@fedoraproject.org> 3.0.5-3
- Added pyxdg requirement
* Sun May 13 2012 Tim Lauridsen <timlau@fedoraproject.org> 3.0.5-1
- bumped version to 3.0.5-1
* Wed May 9 2012 Tim Lauridsen <timlau@fedoraproject.org> 3.0.4-3
- Added PolicyKit policy
- Removed usermode requirement
- Added polkit requirement
* Sat Oct 22 2011 Tim Lauridsen <timlau@fedoraproject.org> 3.0.4-2
- bumped version to 3.0.4-2
- install special yumex.glade on el6
* Tue Oct 11 2011 Tim Lauridsen <timlau@fedoraproject.org> 3.0.4-1
- bumped version to 3.0.4-1
* Wed Apr 27 2011 Tim Lauridsen <timlau@fedoraproject.org> 3.0.3-1
- bumped version to 3.0.3-1
* Wed Mar 30 2011 Tim Lauridsen <timlau@fedoraproject.org> 3.0.2-1
- bumped version to 3.0.2-1
* Thu Jan 6 2011 Tim Lauridsen <timlau@fedoraproject.org> 3.0.1-1
- removed gnome-python2-gconf requirement, not need anymore
* Sun Jan 2 2011 Tim Lauridsen <timlau@fedoraproject.org> 3.0.1-1
- Added urlgrabber requirement
* Tue Dec 21 2010 Tim Lauridsen <timlau@fedoraproject.org> - 3.0.1-1
- bumped version to 3.0.1-1
* Sat Nov 6 2010 Tim Lauridsen <timlau@fedoraproject.org> - 3.0.0-1
- bumped version to 3.0.0-1
* Sat Sep 11 2010 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.11-1
- bumped version to 2.9.11-1
* Fri Jul 30 2010 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.10-1
- bumped version to 2.9.10-1
* Tue Jul 6 2010 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.9-1
- bumped version to 2.9.9-1
* Sat Jun 5 2010 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.8-1
- bumped version to 2.9.8-1
* Mon Jan 31 2010 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.7-1
- bumped version to 2.9.7-1
* Mon Jan 11 2010 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.6-1
- bumped version to 2.9.6-1
* Fri Jan 1 2010 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.5-1
- bumped version to 2.9.5-1 
* Sun Oct 11 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.4-1
- bumped version to 2.9.4-1 
- truncated rpm changelog to 2.9.x releases
* Sun Oct 11 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.3-1
- bumped version to 2.9.3-1 
* Wed Sep 30 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.2-1
- bumped version to 2.9.2-1 
* Fri Sep 18 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.1-1
- bumped version to 2.9.1-1 
* Sun Aug 30 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-1
- bumped version to 2.9.0-1
* Sun Aug 30 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.13.pre
- bumped version to 2.9.0-0.13.pre
* Mon Aug 24 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.12.pre
- bumped version to 2.9.0-0.12.pre
* Fri Aug 21 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.11.pre
- bumped version to 2.9.0-0.11.pre
* Fri Aug 7 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.10.pre
- bumped version to 2.9.0-0.10.pre
* Thu Aug 6 2009 Tim Lauridsen <timlau@fedoraproject.org> - 2.9.0-0.9.pre
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
