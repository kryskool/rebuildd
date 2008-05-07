#!/usr/bin/python

import sys 
 
sys.path.insert(0, "..") 
sys.path.insert(0, ".") 

import unittest
from TestJob import TestJob
from TestDistribution import TestDistribution
from TestRebuildd import TestRebuildd

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJob)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDistribution))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRebuildd))
    unittest.TextTestRunner(verbosity=2).run(suite)
