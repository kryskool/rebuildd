#!/usr/bin/env python2.5
import sys  
  
sys.path.insert(0, "..")  
sys.path.insert(0, ".")  

from RebuilddTestSetup import rebuildd_global_test_setup
import unittest, types, os, socket
from rebuildd.RebuilddConfig import RebuilddConfig
from rebuildd.Rebuildd import Rebuildd
from rebuildd.Package import Package
from rebuildd.Job import Job
from rebuildd.JobStatus import JobStatus

class TestRebuildd(unittest.TestCase):

    def setUp(self):
        rebuildd_global_test_setup()
        self.package = Package(name="zsh", version="4.3.4-10")
        self.r = Rebuildd()

    def test_add_job(self):
        ret = self.r.add_job(name="telak", version="0.5-1", dist="sid")
        self.assert_(ret is True)
        ret = self.r.add_job(name="telak", version="0.5-1", dist="sid")
        self.assert_(ret is False)
        ret = self.r.add_job(name="telak", version="0.5-1", dist="jaydeerulez")
        self.assert_(ret is False)
        ret = self.r.add_job(name="telak", version="0.6-1", dist="sid")
        self.assert_(ret is True)

    def test_clean_jobs(self):
        ret = self.r.clean_jobs()
        self.assert_(ret is True)

    def test_stop_all_jobs(self):
        ret = self.r.stop_all_jobs()
        self.assert_(ret is True)

    def test_release_jobs(self):
        ret = self.r.release_jobs()
        self.assert_(ret is True)

    def test_get_job(self):
        self.r.add_job(name="glibc", version="2.6-3", dist="sid")
        pkg = Package.selectBy(name="glibc", version="2.6-3")[0]
        job = Job.selectBy(package=pkg)[0]
        self.assert_(self.r.get_new_jobs() > 0)
        self.assert_(self.r.get_job(job.id) is job)

    def test_get_new_jobs(self):
        self.r.add_job(name="xpdf", version="3.02-1", dist="lenny")
        self.assert_(self.r.get_new_jobs() >= 1)

    def test_cancel_job(self):
        self.r.add_job(name="glibc", version="2.6-2", dist="sid")
        self.r.get_new_jobs()
        pkg = Package.selectBy(name="glibc", version="2.6-2")[0]
        job = Job.selectBy(package=pkg)[0]
        self.assert_(self.r.cancel_job(job.id) is True)
        self.assert_(self.r.cancel_job(42) is False)

    def test_fix_job(self):
        self.r.add_job(name="glibc", version="2.6.1-3", dist="sid")
        pkg = Package.selectBy(name="glibc", version="2.6.1-3")[0]
        a = Job.selectBy(package=pkg)[0]
        a.status = JobStatus.BUILDING
        a.host = socket.gethostname()

        self.r.add_job(name="xterm", version="1.2-2", dist="sid")
        pkg = Package.selectBy(name="xterm", version="1.2-2")[0]
        b = Job.selectBy(package=pkg)[0]
        b.status = JobStatus.BUILDING
        b.host = "whoisgonnacallaboxlikethis"

        self.r.add_job(name="iceweasel", version="5.0-2", dist="etch")
        pkg = Package.selectBy(name="iceweasel", version="5.0-2")[0]
        c = Job.selectBy(package=pkg)[0]
        c.status = JobStatus.WAIT_LOCKED
        c.host = socket.gethostname()

        self.assert_(self.r.fix_jobs(False) is True)

        self.assert_(a.status is JobStatus.WAIT)
        self.assert_(a.host is None)
        self.assert_(b.status is JobStatus.BUILDING)
        self.assert_(b.host is "whoisgonnacallaboxlikethis")
        self.assert_(c.status is JobStatus.WAIT)
        self.assert_(c.host is None)

        # Reset to a safe state or get_new_jobs will fail after
        a.status = JobStatus.WAIT_LOCKED
        a.host = socket.gethostname()
        b.status = JobStatus.WAIT_LOCKED
        b.host = socket.gethostname()
        c.status = JobStatus.WAIT_LOCKED
        c.host = socket.gethostname()

    def test_build_more_recent(self):
        self.r.get_new_jobs()
        RebuilddConfig().set('build', 'build_more_recent', '1')  

        self.r.add_job(name="recenter", version="2.6.1-3", dist="sid")
        pkg = Package.selectBy(name="recenter", version="2.6.1-3")[0]
        a = Job.selectBy(package=pkg)[0]

        self.r.add_job(name="recenter", version="1:2.6.1-2", dist="sid")
        pkg = Package.selectBy(name="recenter", version="1:2.6.1-2")[0]
        b = Job.selectBy(package=pkg)[0]

        self.r.add_job(name="recenter", version="3.6.1-4", dist="sid")
        pkg = Package.selectBy(name="recenter", version="3.6.1-4")[0]
        c = Job.selectBy(package=pkg)[0]

        self.r.add_job(name="recenter", version="2.6.0-2", dist="sid", arch="any")
        pkg = Package.selectBy(name="recenter", version="2.6.0-2")[0]
        d = Job.selectBy(package=pkg)[0]

        self.assert_(self.r.get_new_jobs() > 0)
        self.assert_(a.status == JobStatus.GIVEUP)
        self.assert_(b.status == JobStatus.WAIT_LOCKED)
        self.assert_(c.status == JobStatus.GIVEUP)
        self.assert_(d.status == JobStatus.WAIT_LOCKED)

        RebuilddConfig().set('build', 'build_more_recent', '0')  

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRebuildd)
    unittest.TextTestRunner(verbosity=2).run(suite)
