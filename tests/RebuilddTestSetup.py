from rebuildd.RebuilddConfig import RebuilddConfig
from rebuildd.Rebuildd import Rebuildd
from rebuildd.Package import Package
from rebuildd.Job import Job
from rebuildd.RebuilddLog import Log
import os

def rebuildd_global_test_setup():
        RebuilddConfig(dontparse=True)
        RebuilddConfig().set('log', 'logs_dir', '/tmp')
        RebuilddConfig().set('build', 'database_uri', 'sqlite:///tmp/rebuildd-tests.db')
        RebuilddConfig().set('build', 'max_jobs', '100')
        RebuilddConfig().set('log', 'file', '/dev/null')
        RebuilddConfig().set('log', 'mail_failed', '0')
        RebuilddConfig().set('build', 'build_more_recent', '0') 
        RebuilddConfig().set('log', 'mail_successful', '0')
        RebuilddConfig().arch = ["alpha", "any"]
        Rebuildd()
        try:
            Package.dropTable(ifExists=True)
            Job.dropTable(ifExists=True)
            Log.dropTable(ifExists=True)
            Package.createTable()
            Job.createTable()
            Log.createTable()
        except:
            pass

def rebuildd_global_test_teardown():
        try:
            Rebuildd()._sqlconnection.dropDatabase()
            Rebuildd()._sqlconnection.close()
	    Rebuildd()._sqlconnection._threadPool = {}
        except:
            pass
                
