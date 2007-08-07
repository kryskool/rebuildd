#!/usr/bin/env python2.5
import sys  
  
sys.path.insert(0, "..")  
sys.path.insert(0, ".")  
from RebuilddTestSetup import rebuildd_global_test_setup
import unittest, types, os
import sqlobject
from rebuildd.RebuilddConfig import RebuilddConfig
from rebuildd.Package import Package
from rebuildd.Job import Job
from rebuildd.Jobstatus import JOBSTATUS

class TestJob(unittest.TestCase):

    def setUp(self):
        rebuildd_global_test_setup()
        self.job = Job(package=Package(name="bash", version="3.1dfsg-8"), arch="alpha", dist="sid")

    def test_init(self):
        self.assert_(type(self.job) is Job)

    def test_setattr(self):
        self.job.build_status = JOBSTATUS.UNKNOWN
        self.assert_(self.job.build_status == JOBSTATUS.UNKNOWN)
        self.job.build_status = JOBSTATUS.WAIT
        self.assert_(self.job.build_status == JOBSTATUS.WAIT)

    def test_open_logfile(self):
        file = self.job.open_logfile("w")
        self.assert_(file is not None)
        filero = self.job.open_logfile("r")
        self.assert_(filero is not None)
        file.close()
        filero.close()
        os.unlink(file.name)

    def test_build_status_on_doquit(self):
        self.job.do_quit.set()
        self.job.start()
        self.job.join()
        self.assert_(self.job.build_status == JOBSTATUS.WAIT_LOCKED)

    def test_build_success(self):
        self.job.do_quit.clear()
        RebuilddConfig().set('build', 'source_cmd', '/bin/true %s %s %s')
        RebuilddConfig().set('build', 'build_cmd', '/bin/true %s %s %s')
        RebuilddConfig().set('build', 'post_build_cmd', '/bin/true %s %s %s')
        self.job.start()
        self.job.join()
        self.assert_(self.job.build_status == JOBSTATUS.OK)

    def test_build_failure1(self):
        self.job.do_quit.clear()
        RebuilddConfig().set('build', 'source_cmd', '/bin/false %s %s %s')
        RebuilddConfig().set('build', 'build_cmd', '/bin/true %s %s %s')
        RebuilddConfig().set('build', 'post_build_cmd', '/bin/true %s %s %s')
        self.job.start()
        self.job.join()
        self.assert_(self.job.build_status == JOBSTATUS.FAILED)

    def test_build_failure2(self):
        self.job.do_quit.clear()
        RebuilddConfig().set('build', 'source_cmd', '/bin/true %s %s %s')
        RebuilddConfig().set('build', 'build_cmd', '/bin/false %s %s %s')
        RebuilddConfig().set('build', 'post_build_cmd', '/bin/true %s %s %s')
        self.job.start()
        self.job.join()
        self.assert_(self.job.build_status == JOBSTATUS.FAILED)

    def test_build_failure3(self):
        RebuilddConfig().set('build', 'source_cmd', '/bin/true %s %s %s')
        RebuilddConfig().set('build', 'build_cmd', '/bin/true %s %s %s')
        RebuilddConfig().set('build', 'post_build_cmd', '/bin/false %s %s %s')
        self.job.start()
        self.job.join()
        self.assert_(self.job.build_status == JOBSTATUS.FAILED)

    def test_send_build_log(self):
        self.assert_(self.job.send_build_log() is False)
        self.job.build_status = JOBSTATUS.BUILD_OK
        self.assert_(self.job.send_build_log() is True)
        self.assert_(self.job.build_status is JOBSTATUS.OK)
        self.job.build_status = JOBSTATUS.BUILD_FAILED
        self.assert_(self.job.send_build_log() is True)
        self.assert_(self.job.build_status is JOBSTATUS.FAILED)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJob)
    unittest.TextTestRunner(verbosity=2).run(suite)
