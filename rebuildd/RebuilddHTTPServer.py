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
from Rebuildd import Rebuildd
from Package import Package
from Job import Job

from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from mako.template import Template

import threading, socket

class RebuilddHTTPHandler(SimpleHTTPRequestHandler):
    """Class used for handling HTTP resquest"""

    def do_GET(self):
        """GET method"""

        try:
            d = {}
            for kwd in ( "job", "host", "arch", "dist"):
                try:
                    index_kwd = self.path.index(kwd)
                except ValueError:
                    continue

                index_start = index_kwd + len(kwd) + 1
                try:
                    index_end = self.path.index("/", index_kwd)
                except ValueError:
                    index_end = None
                
                if kwd == "job":
                    self.send_job(int(self.path[index_start:index_end]))
                    return
                else:
                    d[kwd] = self.path[index_start:index_end]

            self.send_index(**d)

            return
        except Exception, error:
            try:
                self.send_error(500, error.__str__())
            except:
                pass
            return

        self.send_error(404, "Document not found :-(")

    def send_hdrs(self):
        self.send_response(200, 'OK')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def send_job(self, jobid):
        tpl = Template(filename=RebuilddConfig().get('http', 'templates_dir') \
                       + "/job.tpl")
        job = []
        job.extend(Job.selectBy(id=jobid))
        if len(job):
            job = job[0]
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
            try:
                self.send_error(500, "No such job %s" % jobid)
            except:
                pass

    def send_index(self, **kwargs):
        self.send_hdrs()
        tpl = Template(filename=RebuilddConfig().get('http', 'templates_dir') \
                       + "/index.tpl")
        jobs = []
        jobs.extend(Job.selectBy(**kwargs))
        self.wfile.write(tpl.render(host=socket.getfqdn(), \
                                    jobs=jobs))


class RebuilddHTTPServer(threading.Thread, HTTPServer):
    """Main HTTP server"""

    def __init__(self):
        threading.Thread.__init__(self)
        HTTPServer.__init__(self,
                            (RebuilddConfig().get('http', 'ip'),
                             RebuilddConfig().getint('http', 'port')),
                            RebuilddHTTPHandler)
        Rebuildd()

    def run(self):

        """Run main HTTP server thread"""
        
        self.serve_forever()

