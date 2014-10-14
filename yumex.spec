%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:     yumex
Version:  3.0.16
Release:  2%{?dist}
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
Requires: pycairo
Requires: python-pexpect
Requires: python-iniparse
Requires: dbus-python
Requires: python-kitchen
Requires: urlgrabber
Requires: polkit
Requires: pyxdg
Requires(pre): shadow-utils

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

desktop-file-validate %{buildroot}/%{_datadir}/applications/%{name}.desktop
desktop-file-validate %{buildroot}/%{_datadir}/applications/%{name}-local.desktop

    
# this is a doc file; removing from installed tree
rm $RPM_BUILD_ROOT%{_datadir}/yumex/COPYING

%find_lang %name

%pre
getent group yumex >/dev/null || groupadd -r yumex

%post
update-desktop-database %{_datadir}/applications &> /dev/null || :

%postun
update-desktop-database %{_datadir}/applications &> /dev/null || :

%clean
rm -rf $RPM_BUILD_ROOT

%files -f  %{name}.lang
%defattr(-, root, root, -)
%doc COPYING ChangeLog TODO
%{_datadir}/pixmaps/*
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
%{_datadir}/appdata/*.xml
%{_datadir}/polkit-1/rules.d/*.rules

%changelog
* Tue Oct 14 2014 Tim Lauridsen <timlau@fedoraproject.org> 3.0.16-2
- create yumex group
- added shadow-utils requirement (pre)
- added PolicyKit rule
* Sun Oct 5 2014 Tim Lauridsen <timlau@fedoraproject.org> 3.0.16-1
- bumped version to 3.0.16
- removed udisks requirement
- cleaned up the spec changelog
* Wed Jun 4 2014 Tim Lauridsen <timlau@fedoraproject.org> 3.0.15-1
- bumped version to 3.0.15
* Tue Feb 25 2014 Tim Lauridsen <timlau@fedoraproject.org> 3.0.14-1
- bumped version to 3.0.14
* Wed Oct 16 2013 Tim Lauridsen <timlau@fedoraproject.org> 3.0.13-1
- bumped version to 3.0.13
* Mon Oct 07 2013 Tim Lauridsen <timlau@fedoraproject.org> 3.0.12-2
- changed requirement pexpect to python-pexpect


