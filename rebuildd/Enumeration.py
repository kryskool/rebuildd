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

import types

class Enumeration: 
    """Simple enumeration class with reverse lookup""" 

    def __init__(self, enumlist): 
        self.lookup = { } 
        self.reverse_lookup = { } 
        val = 0 
        for elem in enumlist: 
            if type(elem) == types.TupleType: 
                elem, val = elem 
            if type(elem) != types.StringType: 
                raise ValueError("enum name is not a string: " + elem)
            if type(val) != types.IntType: 
                raise ValueError("enum value is not an integer: " + val)
            if self.lookup.has_key(elem): 
                raise ValueError("enum name is not unique: " + elem)
            if val in self.lookup.values(): 
                raise ValueError("enum value is not unique for " + val)
            self.lookup[elem] = val 
            self.reverse_lookup[val] = elem 
            val += 1 

    def __getattr__(self, attr): 
        if not self.lookup.has_key(attr): 
            raise AttributeError 
        return self.lookup[attr] 

    def whatis(self, value): 
        """Return element name for a value""" 

        return self.reverse_lookup[value]
