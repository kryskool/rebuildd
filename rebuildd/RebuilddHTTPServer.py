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
from Jobstatus import JOBSTATUS

import tempfile
import web
import gdchart

render = web.template.render(RebuilddConfig().get('http', 'templates_dir'), \
         cache=RebuilddConfig().getboolean('http', 'cache'))

class RequestIndex:

    def GET(self):
        print render.base(page=render.index(), title="rebuildd")

class RequestDist:

    def GET(self, dist=None):
        print render.base(page=render.dist())

class RequestArch:

    def GET(self, dist, arch=None):
        print render.base(page=render.arch())

class RequestJob:

    def GET(self, jobid=None):
        print render.base(page=render.job())

class RequestGraph:

    GET = web.autodelegate("GET_")

    def GET_buildstats(self, arch=None):
        web.header("Content-Type","image/png") 
        graph = gdchart.Bar3D()
        graph.width = 300
        graph.height = 300
        graph.ytitle = "Jobs"
        graph.xtitle = "Build status"
        graph.ext_color = [ "yellow", "orange", "red", "green"]
        graph.bg_color = "white"
        if arch == "/":
            graph.title = "Build status"
            jobs = Job.selectBy()
        else:
            graph.title = "Build status for %s" % arch[1:]
            jobs = Job.selectBy(arch=arch[1:])

        jw = 0
        jb = 0
        jf = 0
        jo = 0
        for job in jobs:
            if job.build_status == JOBSTATUS.WAIT or \
               job.build_status == JOBSTATUS.WAIT_LOCKED:
                jw += 1
            elif job.build_status == JOBSTATUS.BUILDING:
                jb += 1
            elif job.build_status == JOBSTATUS.BUILD_FAILED or \
                 job.build_status == JOBSTATUS.FAILED:
                jf += 1
            elif job.build_status == JOBSTATUS.BUILD_OK or \
                 job.build_status == JOBSTATUS.OK:
                jo += 1

        graph.setData([jw, jb, jf, jo])
        graph.setLabels(["WAIT", "BUILDING", "FAILED", "OK"])
        tmp = tempfile.TemporaryFile()
        graph.draw(tmp)
        tmp.seek(0)
        print tmp.read()

class RebuilddHTTPServer:
    """Main HTTP server"""

    urls = (
            '/', 'RequestIndex',
            '/dist/(.*)', 'RequestDist',
            '/dist/(.*)/arch/(.*)', 'RequestArch',
            '/job/(.*)', 'RequestJob',
            '/graph/(.*)', 'RequestGraph',
            )

    def __init__(self):
        Rebuildd()

    def start(self):

        """Run main HTTP server thread"""

        web.webapi.internalerror = web.debugerror
        web.httpserver.runsimple(web.webapi.wsgifunc(web.webpyfunc(self.urls, globals(), False)),
                                 (RebuilddConfig().get('http', 'ip'),
                                  RebuilddConfig().getint('http', 'port')))
