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

from __future__ import with_statement

import threading, subprocess, smtplib, time, os, signal, socket, select
import sqlobject
from email.Message import Message
from Dists import Dists
from Jobstatus import JOBSTATUS
from RebuilddLog import RebuilddLog
from RebuilddConfig import RebuilddConfig

__version__ = "$Rev$"

class Job(threading.Thread, sqlobject.SQLObject):
    """Class implementing a build job"""

    build_status = sqlobject.IntCol(default=JOBSTATUS.UNKNOWN)
    do_quit = threading.Event()
    mailto = sqlobject.StringCol(default=None)
    package = sqlobject.ForeignKey('Package')
    dist = sqlobject.StringCol(default='sid')
    arch = sqlobject.StringCol(default='all')
    creation_date = sqlobject.DateTimeCol(default=sqlobject.DateTimeCol.now)
    status_lock = threading.Lock()
    build_start = sqlobject.DateTimeCol(default=None)
    build_end = sqlobject.DateTimeCol(default=None)
    host = sqlobject.StringCol(default=None)
    notify = None

    def __init__(self, *args, **kwargs):
        """Init job"""

        threading.Thread.__init__(self)
        sqlobject.SQLObject.__init__(self, *args, **kwargs)

    def __setattr__(self, name, value):
        """Override setattr to log build status changes"""

        if name == "build_status":
            RebuilddLog().info("Job %s for %s_%s on %s/%s changed status from %s to %s"\
                    % (self.id, self.package.name, self.package.version, 
                       self.dist, self.arch,
                       JOBSTATUS.whatis(self.build_status),
                       JOBSTATUS.whatis(value)))
        sqlobject.SQLObject.__setattr__(self, name, value)

    def open_logfile(self, mode="r"):
        """Open logfile and return file object"""

        build_log_file = "%s/%s_%s-%s-%s-%s.%s.log" % (RebuilddConfig().get('log', 'logs_dir'),
                                           self.package.name, self.package.version,
                                           self.dist, self.arch,
                                           self.creation_date.strftime("%Y%m%d-%H%M%S"),
                                           self.id)
        try:
            build_log = open(build_log_file, mode)
        except Exception, error:
            # Don't log if file does not exist
            if error.errno != 2:
                RebuilddLog().error("Unable to open log file %s for job %s: %s" 
                                     % (build_log_file, self.id, error))
            return None
        return build_log

    def preexec_child(self):
        """Start a new group process before executing child"""

        os.setsid()

    def run(self):
        """Run job thread, download and build the package"""

        build_log = self.open_logfile("w")
        if not build_log:
            return

        # we are building
        with self.status_lock:
            self.build_status = JOBSTATUS.BUILDING

        self.build_start = sqlobject.DateTimeCol.now()

        build_log.write("Automatic build of %s_%s on %s for %s/%s by rebuildd %s\n" % \
                         (self.package.name, self.package.version,
                          self.host, self.dist, self.arch, __version__))
        build_log.write("Build started at %s\n" % self.build_start)
        build_log.write("******************************************************************************\n")

        # execute commands
        for cmd in (Dists().dists[self.dist].get_source_cmd(self.package),
                    Dists().dists[self.dist].get_build_cmd(self.package),
                    Dists().dists[self.dist].get_post_build_cmd(self.package)):
            if cmd is None:
                continue
            try:
                proc = subprocess.Popen(cmd.split(), bufsize=0,
                                                     preexec_fn=self.preexec_child,
                                                     stdout=build_log,
                                                     stdin=None,
                                                     stderr=subprocess.STDOUT)
            except Exception, error:
                state = 1
                break
            state = proc.poll()
            while not self.do_quit.isSet() and state == None:
                state = proc.poll()
                self.do_quit.wait(1)
            if self.do_quit.isSet() or state != 0:
                break

        if self.do_quit.isSet():
            # Kill gently the process
            RebuilddLog().info("Killing job %s with SIGINT" % self.id)
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGINT)
            except OSError, error:
                RebuilddLog().error("Error killing job %s: %s" % (self.id, error))

            # If after 60s it's not dead, KILL HIM
            counter = 0
            while proc.poll() == None and counter < 60:
                time.sleep(1)
                counter += 1
            if proc.poll() == None:
                RebuilddLog().error("Killing job %s timed out, killing with SIGKILL" \
                           % self.id)
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)

            with self.status_lock:
                self.build_status = JOBSTATUS.WAIT_LOCKED

            # Reset host
            self.host = ""

            build_log.write("\nBuild job killed on request\n")
            build_log.close()

            return

        # build is finished
        with self.status_lock:
            if state == 0:
                self.build_status = JOBSTATUS.BUILD_OK
            else:
                self.build_status = JOBSTATUS.BUILD_FAILED

        self.build_end = sqlobject.DateTimeCol.now()

        build_log.write("******************************************************************************\n")
        build_log.write("Finished with status %s at %s\n" % (JOBSTATUS.whatis(self.build_status), self.build_end))
        build_log.write("Build needed %s\n" % (self.build_end - self.build_start))
        build_log.close()


        # Send event to Rebuildd to inform it that it can
        # run a brand new job!
        if self.notify:
            self.notify.set()

        self.send_build_log()

    def send_build_log(self):
        """When job is BUILT, send logs by mail"""

        if self.build_status != JOBSTATUS.BUILD_OK and \
           self.build_status != JOBSTATUS.BUILD_FAILED:
            return False

        with self.status_lock:
            if not RebuilddConfig().getboolean('log', 'mail_successful') \
               and self.build_status == JOBSTATUS.BUILD_OK:
                self.build_status = JOBSTATUS.OK
                return True
            elif not RebuilddConfig().getboolean('log', 'mail_failed') \
                 and self.build_status == JOBSTATUS.BUILD_FAILED:
                self.build_status = JOBSTATUS.FAILED
                return True

        bstatus = "failed"

        if self.build_status == JOBSTATUS.BUILD_OK:
            bstatus = "successful"

        msg = Message()
        if self.mailto:
            msg['To'] = self.mailto
        else:
            msg['To'] = RebuilddConfig().get('mail', 'mailto')
        msg['From'] = RebuilddConfig().get('mail', 'from')
        msg['Subject'] = RebuilddConfig().get('mail', 'subject_prefix') + \
                                 " Log for %s build of %s_%s on %s/%s" % \
                                 (bstatus,
                                  self.package.name, 
                                  self.package.version,
                                  self.dist,
                                  self.arch)
        msg['X-Rebuildd-Version'] = __version__
        msg['X-Rebuildd-Host'] = socket.getfqdn()

        
        build_log = self.open_logfile("r")
        if not build_log:
            return False

        log = ""
        for line in build_log.readlines():
            log += line

        msg.set_payload(log)

        try:
            smtp = smtplib.SMTP()
            smtp.connect()
            if self.mailto:
                smtp.sendmail(RebuilddConfig().get('mail', 'from'),
                              self.mailto,
                              msg.as_string())
            else:
                smtp.sendmail(RebuilddConfig().get('mail', 'from'),
                              RebuilddConfig().get('mail', 'mailto'),
                              msg.as_string())
        except Exception, error:
            RebuilddLog().error("Unable to send build log mail for job %s: %s" % (self.id, error))

        with self.status_lock:

            if self.build_status == JOBSTATUS.BUILD_OK:
                self.build_status = JOBSTATUS.OK
            if self.build_status == JOBSTATUS.BUILD_FAILED:
                self.build_status = JOBSTATUS.FAILED

        return True
