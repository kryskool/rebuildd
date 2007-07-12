#!/usr/bin/env python2.5
import sys  
  
sys.path.insert(0, "..")  
sys.path.insert(0, ".")  

from RebuilddTestSetup import rebuildd_global_test_setup
import unittest, types, os
from rebuildd.RebuilddConfig import RebuilddConfig
from rebuildd.Rebuildd import Rebuildd
from rebuildd.Package import Package
from rebuildd.Job import Job

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
        self.r.get_new_jobs()
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

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRebuildd)
    unittest.TextTestRunner(verbosity=2).run(suite)
