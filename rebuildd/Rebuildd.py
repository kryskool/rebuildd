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

"""rebuildd - Debian packages rebuild tool"""

from __future__ import with_statement

from Enumeration import Enumeration
from Distribution import Distribution
from Dists import Dists
from RebuilddLog import RebuilddLog
from RebuilddConfig import RebuilddConfig
from RebuilddNetworkServer import RebuilddNetworkServer
from RebuilddHTTPServer import RebuilddHTTPServer
from Package import Package
from Job import Job
from Jobstatus import JOBSTATUS
import threading, os, time, sys, sqlobject

__version__ = "$Rev$"

class Rebuildd:
    jobs = []
    do_quit = threading.Event()
    jobs_locker = threading.Lock()
    job_finished = threading.Event()
    _instance = None 
         
    def __new__(cls):  
        if cls._instance is None:  
           cls._instance = object.__new__(cls)  
        return cls._instance  

    def __init__(self):
        self.cfg = RebuilddConfig()
        # Init arch
        self.log = RebuilddLog()

        sqlobject.sqlhub.processConnection = \
            sqlobject.connectionForURI(self.cfg.get('build', 'database_uri')) 

        # Create distributions
        for dist in self.cfg.get('build', 'dists').split(' '):
            Dists().add_dist(Distribution(dist))

    def daemon(self):
        self.log.info("Starting rebuildd %s" % __version__)
        self.daemonize()

        self.log.info("Launching network servers")
        # Run the network server thread
        self.netserv = RebuilddNetworkServer(self)
        self.netserv.setDaemon(True)
        self.netserv.start()
        self.httpd = RebuilddHTTPServer(self)
        self.httpd.setDaemon(True)
        self.httpd.start()

        self.log.info("Running main loop")
        # Run main loop
        self.loop()

    def daemonize(self):
        """Do daemon stuff"""

        try:
            os.chdir(self.cfg.get('build', 'work_dir'))
        except Exception, error:
            print "E: unable to chdir to work_dir: %s" % error
            sys.exit(1)

        try:
            sys.stdout = sys.stderr = file(self.cfg.get('log', 'file'), "a")
            if os.fork():
                sys.exit(0)
        except Exception, error:
            print "E: unable to fork: %s" % error

    def get_job(self, jobid):
        for job in self.jobs:
            if job.id == jobid:
                return job

        return None

    def read_new_jobs(self):
        """Feed jobs list with waiting jobs"""

        with self.jobs_locker:
            jobs = []
            for arch in (self.cfg.arch, "all"):
                jobs.extend(Job.selectBy(build_status=JOBSTATUS.WAIT, arch=arch))
            count_new = 0
            for job in jobs:
                if self.get_job(job.id) == None:
                    self.jobs.append(job)
                    count_new += 1

        return count_new

    def count_running_jobs(self):
        """Count running jobs"""

        count = 0
        with self.jobs_locker:
            for job in self.jobs:
                if job.build_status == JOBSTATUS.BUILDING and job.isAlive():
                    count += 1

        return count

    def start_jobs(self, overrun=0):
        """Start waiting jobs"""

        running_threads = self.count_running_jobs()
        max_threads = max(overrun, int(self.cfg.get('build', 'max_threads')))
        jobs_started = 0

        with self.jobs_locker:
            for job in self.jobs:
                if running_threads >= max_threads:
                    break
            
                with job.status_lock:
                    if job.build_status == JOBSTATUS.WAIT and not job.isAlive():
                        self.log.info("Starting new thread for job %s" % job.id)
                        job.set_notify(self.job_finished)
                        job.setDaemon(True)
                        job.start()
                        jobs_started += 1
                        running_threads = running_threads + 1

        self.log.info("Running threads: %s/%s" % (running_threads, max_threads))

        return jobs_started

    def send_build_logs(self):
        """Send all finished build logs"""

        with self.jobs_locker:
            for job in self.jobs:
                job.send_build_log()

    def dump_jobs(self):
        """Dump all jobs status"""

        ret = ""
        with self.jobs_locker:
            for job in self.jobs:
                ret = ret + "I: Job %s for %s_%s is status %s on %s/%s for %s\n" % \
                            (job.id,
                             job.package.name,
                             job.package.version,
                             JOBSTATUS.whatis(job.build_status),
                             job.dist,
                             job.arch,
                             job.mailto)

        return ret

    def cancel_job(self, jobid):
        """Cancel a job"""

        with self.jobs_locker:
            job = self.get_job(jobid)
            if job != None:
                if job.isAlive():
                    job.do_quit.set()
                    job.join()
                job.build_status = JOBSTATUS.CANCELED
                self.jobs.remove(job)
                self.log.info("Canceled job %s for %s_%s on %s/%s for %s" \
                                % (job.id, job.package.name, job.package.version,
                                job.dist, job.arch, job.mailto))
                return True

        return False

    def stop_all_jobs(self):
        """Stop all running jobs"""

        with self.jobs_locker:
            for job in self.jobs:
                if job.build_status == JOBSTATUS.BUILDING and job.isAlive():
                    job.do_quit.set()
                    self.log.info("Sending stop to job %s" % job.id)
            for job in self.jobs:
                if job.isAlive():
                    self.log.info("Waiting for job %s to terminate" % job.id)
                    job.join(60)

        return True

    def add_job(self, name, version, dist, mailto=None, arch=None):
        """Add a job"""

        if not Dists().dists.has_key(dist):
            return False

        if not arch:
            arch = self.cfg.arch

        pkgs = Package.selectBy(name=name, version=version)
        if pkgs.count():
            # If several packages exists, just take the first
            pkg = pkgs[0]
        else:
            # Maybe we found no packages, so create a brand new one!
            pkg = Package(name=name, version=version)

        job = Job(package=pkg, dist=dist, arch=arch)
        job.build_status = JOBSTATUS.WAIT
        job.arch = arch
        job.mailto = mailto

        self.log.info("Added job for %s_%s on %s/%s for %s" \
                   % (name, version, dist, arch, mailto))
        return True

    def clean_jobs(self):
        """Clean finished or canceled jobs"""

        with self.jobs_locker:
            for job in self.jobs:
                if job.build_status == JOBSTATUS.OK \
                   or job.build_status == JOBSTATUS.FAILED \
                   or job.build_status == JOBSTATUS.CANCELED:
                    self.jobs.remove(job)

        return True

    def loop(self):
        """Rebuildd main loop"""

        counter = int(self.cfg.get('build', 'check_every'))
        while not self.do_quit.isSet():
            if counter == int(self.cfg.get('build', 'check_every')) \
               or self.job_finished.isSet():
                self.read_new_jobs()
                # Start jobs
                self.start_jobs()
                # Try to resend build logs if failed
                self.send_build_logs()
                # Clean finished jobs
                self.clean_jobs()
                counter = 0
                self.job_finished.clear()
            self.do_quit.wait(1)
            counter += 1

        self.log.info("Killing rebuildd")
        # On exit
        self.log.info("Sending last logs")
        self.send_build_logs()
        self.log.info("Cleaning finished and canceled jobs")
        self.clean_jobs()
        self.log.info("Stopping all jobs")
        self.stop_all_jobs()
        self.netserv.join(10)
        self.httpd.join(10)
        self.log.info("Exiting rebuildd")

