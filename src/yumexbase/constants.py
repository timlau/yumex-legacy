#!/usr/bin/python -tt
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# (C) 2009 - Tim Lauridsen <timlau@fedoraproject.org>

# Yum Extender Constants

'''
Yum Extender Constants
'''

import os
import sys
import pango
import time
from xdg import BaseDirectory

# We want these lines, but don't want pylint to whine about the imports not being used
# pylint: disable-msg=W0611
from yumexbase import _, P_  # lint:ok
# pylint: enable-msg=W0611

from yum.constants import *

# Constant

__yumex_version__ = "3.0.10"

YUMEX_LOG = 'yumex.verbose'
FILTER_ACTIONS = {'updates' : 'u', 'available': 'i', 'installed' : 'r', \
                   'obsoletes' : 'o', 'downgrade'  : 'do', 'reinstall' : 'ri', 'localinstall' : 'li'}

ACTIONS_FILTER = { 'u' : 'updates', 'i' : 'available', \
                   'r' : 'installed' , 'o' : 'obsoletes', \
                    'do' : 'downgrade', 'ri' : 'reinstall', 'li' : 'localinstall' }

# Paths
BIN_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

if BIN_PATH.endswith('/bin'):
    IS_PROD = True
else:
    IS_PROD = False

if IS_PROD:
    MAIN_PATH = '/usr/share/yumex'
else:
    MAIN_PATH = BIN_PATH

BUILDER_FILE = MAIN_PATH + '/yumex.glade'
BUILDER_PKGINST = MAIN_PATH + '/pkginst.glade'

if IS_PROD:
    PIXMAPS_PATH = '/usr/share/pixmaps/yumex'
elif MAIN_PATH.endswith('test'):
    PIXMAPS_PATH = MAIN_PATH + '/../../gfx'
else:
    PIXMAPS_PATH = MAIN_PATH + '/../gfx'

OLD_CONF_FILE = os.environ['HOME'] + "/.yumex.conf"
CONF_DIR = BaseDirectory.save_config_path('yumex')
CONF_FILE = os.path.join(CONF_DIR,'yumex.conf')
TIMESTAMP_FILE = os.path.join(CONF_DIR,'update_timestamp.conf')
MIN_UPDATE_INTERVAL = 5


# icons
ICON_YUMEX = PIXMAPS_PATH + "/yumex-icon.png"
ICON_PACKAGES = PIXMAPS_PATH + '/button-packages.png'
ICON_GROUPS = PIXMAPS_PATH + '/button-group.png'
ICON_QUEUE = PIXMAPS_PATH + '/button-queue.png'
ICON_OUTPUT = PIXMAPS_PATH + '/button-output.png'
ICON_REPOS = PIXMAPS_PATH + '/button-repo.png'
ICON_HISTORY = PIXMAPS_PATH + '/button-history.png'
ICON_SPINNER = PIXMAPS_PATH + '/spinner.gif'
ICON_SMALL_SPINNER = PIXMAPS_PATH + '/spinner-small.gif'
ICON_TRAY_ERROR = PIXMAPS_PATH + '/tray-error.png'
ICON_TRAY_NO_UPDATES = PIXMAPS_PATH + '/tray-no-updates.png'
ICON_TRAY_UPDATES = PIXMAPS_PATH + '/tray-updates.png'
ICON_TRAY_WORKING = PIXMAPS_PATH + '/tray-working.png'

# NOTE: The package filter radio buttons in the top of the package page
PKG_FILTERS_STRINGS = (_('updates'), _('available'), _('installed'))
PKG_FILTERS_ENUMS = ('updates', 'available', 'installed')

REPO_HIDE = ['source', 'debuginfo']

RECENT_LIMIT = time.time() - (3600 * 24 * 14)
# Max Window size
#gdkRootWindow = gtk._root_window()
#MAX_HEIGHT = gdkRootWindow.height
#MAX_WIDHT = gdkRootWindow.width
#DEFAULT_FONT = gdkRootWindow.get_pango_context().get_font_description()

# Fonts
XSMALL_FONT = pango.FontDescription("sans 6")
SMALL_FONT = pango.FontDescription("sans 8")
BIG_FONT = pango.FontDescription("sans 12")

# STRINGS

REPO_INFO_MAP = {
    'repomd'        : _("Downloading repository information for the %s repository"),
    'primary'       : _("Downloading Package information for the %s repository"),
    'primary_db'    : _("Downloading Package information for the %s repository"),
    'filelists'     : _("Downloading Filelist information for the %s repository"),
    'filelists_db'     : _("Downloading Filelist information for the %s repository"),
    'other'         : _("Downloading Changelog information for the %s repository"),
    'other_db'         : _("Downloading Changelog information for the %s repository"),
    'group'         : _("Downloading Group information for the %s repository"),
    'metalink'      : _("Downloading metalink information for the %s repository"),
    'presto'        : _("Downloading Delta update information for the %s repository"),
    'prestodelta'   : _("Downloading Delta update information for the %s repository"),
    'updateinfo'    : _("Downloading Update information for the %s repository")
}

TASK_PENDING = 1
TASK_RUNNING = 2
TASK_COMPLETE = 3
TASK_ICONS = {TASK_PENDING  : 'gtk-media-stop',
              TASK_RUNNING  : 'gtk-refresh',
              TASK_COMPLETE : 'gtk-yes' }

CATEGORY_AGE = [
            ('1', _('0 - 7 Days')),
            ('2', _('7 - 14 Days')),
            ('3', _('14 - 21 Days')),
            ('4', _('21  - 30 days')),
            ('5', _('30 - 90 days')),
            ('6', _('90+ days'))]

CATEGORY_SIZE = [
    ('1', '0 KB - 100 KB'),
    ('2', '100 KB - 1 MB'),
    ('3', '1 MB - 10 MB'),
    ('4', '10 MB - 50 MB'),
    ('5', '50+ MB')]

SIZE_RANGES = {
   '1' : (0, 100 * 1024),
   '2' : (100 * 1024, 1024 * 1024),
   '3' : (1024 * 1024, 10 * 1024 * 1024),
   '4' : (10 * 1024 * 1024, 50 * 1024 * 1024),
   '5' : (50 * 1024 * 1024, 1024 * 1024 * 1024)
}

HISTORY_KEYS = ['True-Install', 'Install', 'Update', 'Erase', \
'Dep-Install', 'Reinstall', 'Obsoleted', 'Downgrade', \
 'Updated', 'Downgraded', 'Obsoleting']

PACKAGE_LOAD_MSG = {
 'all'          : _('Getting all packages'),
 'installed'    : _('Getting installed packages'),
 'available'    : _('Getting available packages'),
 'updates'      : _('Getting available updates'),
 'obsoletes'    : _('Getting available obsoletes')
 }

# RPM Completed action messages
RPM_ACTIONS = {
    TS_UPDATE: _('%s is updated'),
    TS_ERASE: _('%s is erased'),
    TS_INSTALL: _('%s is installed'),
    TS_TRUEINSTALL: _('%s is installed'),
    TS_OBSOLETED: _('%s is obsoleted'),
    TS_OBSOLETING: _('%s is installed'),
    TS_UPDATED: _('%s is cleanup')
}

HISTORY_NEW_STATES = ['Update', 'Downgrade', 'Obsoleting']
HISTORY_OLD_STATES = ['Updated', 'Downgraded', 'Obsoleted']

HISTORY_UPDATE_STATES = ['Update', 'Downgrade', 'Updated', 'Downgraded']

HISTORY_SORT_ORDER = ['Install', 'True-Install', 'Reinstall', 'Update', 'Downgrade', 'Obsoleting', 'Obsoleted', 'Erase', 'Dep-Install' ]

HISTORY_STATE_LABLES = {
     'Update' : _('Updated packages'),
     'Downgrade' : _('Downgraded packages'),
     'Obsoleting' : _('Obsoleting packages'),
     'Obsoleted' : _('Obsoleted packages'),
     'Erase' : _('Erased packages'),
     'Install' : _('Installed packages'),
     'True-Install' : _('Installed packages'),
     'Dep-Install' : _('Installed for dependencies'),
     'Reinstall' : _('Reinstalled packages')}


# Queue autocomplete lookup
QUEUE_COMMANDS = {
'ins' : 'install',
'era' : 'erase',
'upd' : 'update',
'rem' : 'remove',
'rei' : 'reinstall',
'dow' : 'downgrade'
}

QUEUE_PACKAGE_TYPES = {
'i' : 'install',
'u' : 'update',
'r' : 'remove',
'o' : 'obsolete',
'ri' : 'reinstall',
'do' : 'downgrade',
'li' : 'localinstall'
}

YUMEX_CMDLINE_CMDS = ['search', 'install', 'remove', 'update', 'downgrade', 'reinstall']

SEARCH_KEYS_VALUES = {
    'name' : _("Name"),
    'summary' : _("Summary"),
    'description' : _("Description"),
    'arch' : _("Arch")}

SEARCH_KEYS_ORDER = ['name', 'summary', 'description', 'arch']


