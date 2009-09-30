Name:           gnome-manual-duplex
# List of additional build dependencies
BuildRequires: gtk2-devel cups
Version:        0.0
Release:        1
License:        GPL v2 or later
Source:         gnome-manual-duplex-%{version}.tar.gz
Group:          Productivity/Other
Summary:        test

BuildRoot:      %{_tmppath}/%{name}-%{version}-build

%description
test


%prep
%setup -q

%build

# Assume that the package is built by plain 'make' if there's no ./configure.
# This test is there only because the wizard doesn't know much about the
# package, feel free to clean it up
if test -x ./configure; then
    %configure
fi
make

    

%install

make DESTDIR=$RPM_BUILD_ROOT install

%files
/usr/bin/gnome-manual-duplex
/usr/lib/bonobo/servers/gmd.server
/usr/lib/cups/backend/gmd
/usr/share/applications/gnome-manual-duplex.desktop
/usr/share/gnome-manual-duplex/gmd-applet.py
/usr/share/gnome-manual-duplex/gnome-manual-duplex.xml
/usr/share/gnome-manual-duplex/long_edge.xpm
/usr/share/gnome-manual-duplex/short_edge.xpm
/usr/share/pixmaps/gmd.svg
/usr/share/pixmaps/gnome-manual-duplex.png
