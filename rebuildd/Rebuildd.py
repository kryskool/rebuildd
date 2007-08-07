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
from Package import Package
from Job import Job
from Jobstatus import JOBSTATUS
import threading, os, time, sys, signal, socket
import sqlobject

__version__ = "$Rev$"

class Rebuildd(object):
    jobs = []
    do_quit = threading.Event()
    jobs_locker = threading.Lock()
    job_finished = threading.Event()
    _instance = None 
         
    def __new__(cls):  
        if cls._instance is None:  
           cls._instance = object.__new__(cls)  
           cls._instance.init()
        return cls._instance  

    def init(self):
        self.cfg = RebuilddConfig()

        sqlobject.sqlhub.processConnection = \
            sqlobject.connectionForURI(self.cfg.get('build', 'database_uri')) 

        # Create distributions
        for dist in self.cfg.get('build', 'dists').split(' '):
            Dists().add_dist(Distribution(dist))

    def daemon(self):
        RebuilddLog().info("Starting rebuildd %s" % __version__)
        self.daemonize()

        # Run the network server thread
        RebuilddLog().info("Launching network server")
        self.netserv = RebuilddNetworkServer(self)
        self.netserv.setDaemon(True)
        self.netserv.start()

        # Run main loop
        RebuilddLog().info("Running main loop")
        self.loop()

        # On exit
        RebuilddLog().info("Sending last logs")
        self.send_build_logs()
        RebuilddLog().info("Cleaning finished and canceled jobs")
        self.clean_jobs()
        RebuilddLog().info("Stopping all jobs")
        self.stop_all_jobs()
        RebuilddLog().info("Releasing wait-locked jobs")
        self.release_jobs()
        self.netserv.join(10)
        RebuilddLog().info("Exiting rebuildd")

    def daemonize(self):
        """Do daemon stuff"""

        signal.signal(signal.SIGTERM, self.handle_sigterm)
        signal.signal(signal.SIGINT, self.handle_sigterm)

        try:
            os.chdir(self.cfg.get('build', 'work_dir'))
        except Exception, error:
            print "E: unable to chdir to work_dir: %s" % error
            sys.exit(1)

        try:
            sys.stdout = sys.stderr = file(self.cfg.get('log', 'file'), "a")
        except Exception, error:
            print "E: unable to open logfile: %s" % error

    def get_job(self, jobid):
        for job in self.jobs:
            if job.id == jobid:
                return job

        return None

    def get_all_jobs(self, **kwargs):
        jobs = []
        jobs.extend(Job.selectBy(**kwargs))
        return jobs

    def get_new_jobs(self):
        """Feed jobs list with waiting jobs and lock them"""

        max_new = self.cfg.getint('build', 'max_jobs')
        count_current = len(self.jobs)

        with self.jobs_locker:
            if count_current >= max_new:
                return 0

            jobs = []
            for arch in (self.cfg.arch, "all"):
                jobs.extend(Job.selectBy(build_status=JOBSTATUS.WAIT, arch=arch)[:max_new])

            count_new = 0
            for job in jobs:
                if count_current < max_new and self.get_job(job.id) == None:
                    job.build_status = JOBSTATUS.WAIT_LOCKED
                    job.host = socket.gethostname()
                    self.jobs.append(job)
                    count_new += 1
                    count_current += 1
                else:
                    break

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
        max_threads = max(overrun, self.cfg.getint('build', 'max_threads'))
        jobs_started = 0

        with self.jobs_locker:
            for job in self.jobs:
                if running_threads >= max_threads:
                    break
            
                with job.status_lock:
                    if job.build_status == JOBSTATUS.WAIT_LOCKED and not job.isAlive():
                        RebuilddLog().info("Starting new thread for job %s" % job.id)
                        job.notify = self.job_finished
                        job.setDaemon(True)
                        job.start()
                        jobs_started += 1
                        running_threads = running_threads + 1

        RebuilddLog().info("Running threads: %s/%s" % (running_threads, max_threads))

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
                with job.status_lock:
                    job.build_status = JOBSTATUS.CANCELED
                self.jobs.remove(job)
                RebuilddLog().info("Canceled job %s for %s_%s on %s/%s for %s" \
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
                    RebuilddLog().info("Sending stop to job %s" % job.id)
            for job in self.jobs:
                if job.isAlive():
                    RebuilddLog().info("Waiting for job %s to terminate" % job.id)
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

        jobs = []
        jobs.extend(Job.selectBy(package=pkg, dist=dist, arch=arch, mailto=mailto, build_status=JOBSTATUS.WAIT))
        jobs.extend(Job.selectBy(package=pkg, dist=dist, arch=arch, mailto=mailto, build_status=JOBSTATUS.WAIT_LOCKED))
        jobs.extend(Job.selectBy(package=pkg, dist=dist, arch=arch, mailto=mailto, build_status=JOBSTATUS.BUILDING))
        if len(jobs):
            RebuilddLog().error("Job already existing for %s_%s on %s/%s, don't adding it" \
                           % (pkg.name, pkg.version, dist, arch))
            return False

        job = Job(package=pkg, dist=dist, arch=arch)
        job.build_status = JOBSTATUS.WAIT
        job.arch = arch
        job.mailto = mailto

        RebuilddLog().info("Added job for %s_%s on %s/%s for %s" \
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

    def release_jobs(self):
        """Release jobs"""

        with self.jobs_locker:
            for job in self.jobs:
                with job.status_lock:
                    if job.build_status == JOBSTATUS.WAIT_LOCKED:
                        job.build_status = JOBSTATUS.WAIT
                        job.host = ""

        return True

    def handle_sigterm(self, signum, stack):
        RebuilddLog().info("Receiving transmission... it's a signal %s capt'ain! EVERYONE OUT!" % signum)
        self.do_quit.set()

    def loop(self):
        """Rebuildd main loop"""

        counter = self.cfg.getint('build', 'check_every')
        while not self.do_quit.isSet():
            if counter == self.cfg.getint('build', 'check_every') \
               or self.job_finished.isSet():
                self.get_new_jobs()
                # Start jobs
                self.start_jobs()
                # Clean finished jobs
                self.clean_jobs()
                counter = 0
                self.job_finished.clear()
            self.do_quit.wait(1)
            counter += 1


