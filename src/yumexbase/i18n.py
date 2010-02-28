#!/usr/bin/env python
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# This is a ripped from the yum.i18n and changed to use the yumex translation domain 

'''
'''


def dummy_wrapper(txt):
    '''
    Dummy Translation wrapper, just returning the same string.
    '''
    return to_unicode(txt)

def dummyP_wrapper(str1, str2, n):
    '''
    Dummy Plural Translation wrapper, just returning the singular or plural
    string.
    '''
    if n == 1:
        return str1
    else:
        return str2
    
def to_unicode(obj, encoding = 'utf-8', errors = 'replace'):
    ''' convert a 'str' to 'unicode' '''
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding, errors)
    return obj

    
try: 
    # Setup the yum translation domain and make _() and P_() translation wrappers
    # available.
    # using ugettext to make sure translated strings are in Unicode.
    import gettext
    t = gettext.translation('yumex', fallback = True)
    _ = t.ugettext
    P_ = t.ungettext
except:
    # Something went wrong so we make a dummy _() wrapper there is just
    # returning the same text
    print "Using dummy translation wrappers"
    _ = dummy_wrapper
    P_ = dummyP_wrapper


if __name__ == '__main__':
    pass
