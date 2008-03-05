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

from RebuilddConfig import RebuilddConfig
from RebuilddLog import RebuilddLog
from string import Template

class Distribution(object):
    """Class implementing a Debian distribution

    Substitutions are done in the command strings:

      $d => The distro's name
      $a => the target architecture
      $p => the package's name
      $v => the package's version
    """

    def __init__(self, name, arch):
        self.name = name
        self.arch = arch

    def get_source_cmd(self, package):
        """Return command used for grabing source for this distribution"""

        try:
	    args = { 'd': self.name, 'a': self.arch, 'v': package.version, \
                'p': package.name }
            t = Template(RebuilddConfig().get('build', 'source_cmd'))
	    return t.safe_substitute(**args)
        except TypeError, error:
            RebuilddLog.error("get_source_cmd has invalid format: %s" % error)
            return None
 
    def get_build_cmd(self, package):
        """Return command used for building source for this distribution"""

        # Strip epochs (x:) away
        try:
            index = package.version.index(":")
            args = { 'd': self.name, 'a': self.arch, \
                'v': package.version[index+1:], 'p': package.name }
            t = Template(RebuilddConfig().get('build', 'build_cmd'))
	    return t.safe_substitute(**args)
        except ValueError:
            pass

        try:
            args = { 'd': self.name, 'a': self.arch, \
                'v': package.version, 'p': package.name }
            t = Template(RebuilddConfig().get('build', 'build_cmd'))
	    return t.safe_substitute(**args)
        except TypeError, error:
            RebuilddLog.error("get_build_cmd has invalid format: %s" % error)
            return None

    def get_post_build_cmd(self, package):
        """Return command used after building source for this distribution"""

        cmd = RebuilddConfig().get('build', 'post_build_cmd')
        if cmd == '':
            return None
        try:
            args = { 'd': self.name, 'a': self.arch, \
                'v': package.version, 'p': package.name }
            t = Template(cmd)
	    return t.safe_substitute(**args)
        except TypeError, error:
            RebuilddLog.error("post_build_cmd has invalid format: %s" % error)
            return None
