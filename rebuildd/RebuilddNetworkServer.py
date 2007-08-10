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

import threading, socket
from RebuilddConfig import RebuilddConfig
from RebuilddNetworkClient import RebuilddNetworkClient

class RebuilddNetworkServer(threading.Thread):
    """Main network server listening for connection"""

    def __init__(self, rebuildd):
        threading.Thread.__init__(self)
        self.rebuildd = rebuildd

    def run(self):
        """Run main network server thread"""

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(1)
        self.socket.bind((RebuilddConfig().get('telnet', 'ip'),
                          RebuilddConfig().getint('telnet', 'port')))
        self.socket.listen(2)
        while not self.rebuildd.do_quit.isSet():
            try:
                (client_socket, client_info) = self.socket.accept()
                if client_socket:
                    interface = RebuilddNetworkClient(client_socket,
                                                      self.rebuildd)
                    interface.setDaemon(True)
                    interface.start()
            except socket.timeout:
                pass

        self.socket.close()
