from rebuildd.RebuilddConfig import RebuilddConfig
from rebuildd.Rebuildd import Rebuildd
from rebuildd.Package import Package
from rebuildd.Job import Job
import os

def rebuildd_global_test_setup():
        RebuilddConfig(dontparse=True)
        RebuilddConfig().set('log', 'logs_dir', '/tmp')
        RebuilddConfig().set('build', 'database_uri', 'sqlite:///tmp/rebuildd-tests.db')
        RebuilddConfig().set('log', 'file', '/dev/null')
        RebuilddConfig().set('log', 'mail_failed', '0')
        RebuilddConfig().set('log', 'mail_successful', '0')
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
