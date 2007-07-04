#!/usr/bin/env python
#
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

import ConfigParser
import os, socket

class RebuilddConfig(ConfigParser.ConfigParser):
    """Main configuration singleton"""

    config_file = os.environ['HOME'] + "/.rebuilddrc"
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        ConfigParser.ConfigParser.__init__(self)

        # add default sections
        self.add_section('build')
        self.add_section('mail')
        self.add_section('telnet')
        self.add_section('http')
        self.add_section('log')

        # add default values
        self.set('build', 'check_every', '300')
        self.set('build', 'max_threads', '2')
        self.set('build', 'source_cmd', 'apt-get -qq -t %s source %s=%s')
        self.set('build', 'build_cmd', 'pbuilder build --basetgz /tmp/%s.tgz %s_%s.dsc')
        self.set('build', 'post_build_cmd', '')
        self.set('build', 'dists', 'etch lenny sid')
        self.set('build', 'work_dir', '/tmp')
        self.set('build', 'database_uri', 'sqlite://%s/rebuildd.db' \
                                           % os.environ['HOME'])

        self.set('mail', 'from', 'rebuildd@%s' % socket.getfqdn())
        self.set('mail', 'mailto', 'rebuildd@%s' % socket.getfqdn())
        self.set('mail', 'subject_prefix', '[rebuildd]')

        self.set('telnet', 'port', '9999')
        self.set('telnet', 'ip', '0.0.0.0')
        self.set('telnet', 'prompt', 'rebuildd@%s->' % socket.gethostname())
        self.set('telnet', 'motd', 'Connected on rebuildd on %s' \
                                    % socket.getfqdn())

        self.set('http', 'port', '9998')
        self.set('http', 'ip', '0.0.0.0')
        # This is dedicated to MadCoder
        self.set('http', 'log_lines_nb', '30')
        self.set('http', 'templates_dir', '%s/templates' \
                                          % os.environ['HOME'])

        self.set('log', 'file', os.environ['HOME'] + "/rebuildd.log")
        self.set('log', 'time_format', "%d-%m-%Y %H:%M:%S")
        self.set('log', 'logs_dir', "%s/logs" % os.environ['HOME'])
        self.set('log', 'mail', '1')

        parch = os.popen("dpkg --print-architecture")
        self.arch = parch.readline().strip()
        parch.close()

        self.reload()
        self.save()

    def reload(self):
        """Reload configuration file"""

        return self.read(self.config_file)

    def dump(self):
        """Dump running configuration"""

        conf = ""
        for section in self.sections():
            conf += "[" + section + "]\n"
            for item, value in self.items(section):
                conf += "%s = %s\n" % (item, value)
            conf += "\n"
        return conf

    def save(self):
        """Save configuration file"""

        try:
            self.write(file(self.config_file, 'w'))
        except Excepction, error:
            return False
        return True
