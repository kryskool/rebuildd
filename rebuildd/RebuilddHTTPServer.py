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

from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from mako.template import Template

import threading, socket

class RebuilddHTTPHandler(SimpleHTTPRequestHandler):
    """Class used for handling HTTP resquest"""

    def do_GET(self):
        """GET method"""

        try:
            if self.path == "/":
                self.send_index()
                return
            if self.path[1:].startswith("job_"):
                index = self.path.rindex('_') + 1
                self.send_job(self.path[index:])
                return
        except Exception, error:
            self.send_error(500, error)

        self.send_error(404, "Document not found :-(")

    def send_hdrs(self):
        self.send_response(200, 'OK')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def send_job(self, jobid):
        tpl = Template(filename=RebuilddConfig().get('http', 'templates_dir') \
                       + "/job.tpl")
        job = RebuilddHTTPServer.http_rebuildd.get_job(int(jobid))
        if job:
            build_log = job.open_logfile("r")
            if build_log:
                log = ""
                nblines = RebuilddConfig().getint('http', 'log_lines_nb')
                for line in build_log.readlines()[-nblines:]:
                    log += line
            else:
                log = "No build log available"
            self.send_hdrs()
            self.wfile.write(tpl.render(job=job, log=log))
        else:
            self.send_error(500, "No such job %s" % jobid)

    def send_index(self):
        self.send_hdrs()
        tpl = Template(filename=RebuilddConfig().get('http', 'templates_dir') \
                       + "/index.tpl")
        self.wfile.write(tpl.render(host=socket.getfqdn(), \
                                    jobs=RebuilddHTTPServer.http_rebuildd.jobs))

class RebuilddHTTPServer(threading.Thread, HTTPServer):
    """Main HTTP server"""

    def __init__(self, rebuildd):
        threading.Thread.__init__(self)
        HTTPServer.__init__(self,
                            (RebuilddConfig().get('http', 'ip'),
                             RebuilddConfig().getint('http', 'port')),
                            RebuilddHTTPHandler)
        self.rebuildd = rebuildd
        RebuilddHTTPServer.http_rebuildd = rebuildd

    def run(self):

        """Run main HTTP server thread"""
        
        httpsocket = socket.fromfd(self.fileno(), socket.AF_INET, socket.SOCK_STREAM)
        httpsocket.settimeout(0.1)

        while not self.rebuildd.do_quit.isSet():
            self.handle_request()
            self.rebuildd.do_quit.wait(0.1)

