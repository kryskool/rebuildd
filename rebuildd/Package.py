# rebuildd - Debian packages rebuild tool 
# 
# (c) 2007 - Julien Danjou <acid@debian.org> 
# 
#   This software is free software; you can redistribute it and/or modify 
#   it under the terms of the GNU General Public License as published by 
#   the Free Software Foundation; version 2 dated June, 1991. 
# 
#   This software is distributed in the hope that it will be useful, 
#   but WITHOUT ANY WARRANTY; without even the implied warranty of 
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#   GNU General Public License for more details. 
# 
#   You should have received a copy of the GNU General Public License 
#   along with this software; if not, write to the Free Software 
#   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA 
# 

import sqlobject

import apt_pkg
apt_pkg.init_system()

class Package(sqlobject.SQLObject): 
    """Class implemeting a Debian package""" 
 
    name = sqlobject.StringCol() 
    version = sqlobject.StringCol(default=None) 
    priority = sqlobject.StringCol(default=None)

    @staticmethod
    def version_compare(a, b):
        return apt_pkg.version_compare(a.version, b.version)
