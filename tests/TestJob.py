#!/usr/bin/env python2.5
import sys

sys.path.append("..")

import unittest
import os
import sqlobject
from rebuildd.Rebuildd import Rebuildd
from rebuildd.RebuilddConfig import RebuilddConfig
from rebuildd.Package import Package
from rebuildd.Job import Job
from rebuildd.Jobstatus import JOBSTATUS

class TestJob(unittest.TestCase):

    def setUp(self):
        RebuilddConfig(dontparse=True).set('log', 'logs_dir', '/tmp')
        RebuilddConfig(dontparse=True).set('build', 'database_uri', 'sqlite:///tmp/rebuildd-tests.db')
        RebuilddConfig().set('log', 'file', '/tmp/rebuildd-tests.log')
        try:
            os.unlink("/tmp/rebuildd-tests.db")
        except OSError:
            pass
        Rebuildd()
        try:
            Package.createTable()
            Job.createTable()
        except:
            pass
        self.job = Job(package=Package(name="bash", version="3.1dfsg-8"), arch="alpha", dist="sid")

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

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJob)
    unittest.TextTestRunner(verbosity=2).run(suite)
