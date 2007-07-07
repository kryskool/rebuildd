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

from RebuilddLog import RebuilddLog
from RebuilddConfig import RebuilddConfig

class Distribution(object):
    """Class implementing a Debian distribution"""

    def __init__(self, name):
        self.name = name

    def get_source_cmd(self, package):
        """Return command used for grabing source for this distribution"""

        return RebuilddConfig().get('build', 'source_cmd') \
                % (self.name, package.name, package.version)
 
    def get_build_cmd(self, package):
        """Return command used for building source for this distribution"""

        # Strip epochs (x:) away
        try:
            index = RebuilddConfig().get('build', 'build_cmd').index(":")
            return RebuilddConfig().get('build', 'build_cmd')[index+1:] \
                    % (self.name, package.name, package.version)
        except ValueError:
            pass

        return RebuilddConfig().get('build', 'build_cmd') \
                % (self.name, package.name, package.version)

    def get_post_build_cmd(self, package):
        """Return command used after building source for this distribution"""

        return RebuilddConfig().get('build', 'build_cmd') \
                % (self.name, package.name, package.version)
