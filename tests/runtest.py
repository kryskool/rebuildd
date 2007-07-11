#!/usr/bin/env python2.5

import sys 
 
sys.path.insert(0, "..") 
sys.path.insert(0, ".") 

import unittest
from TestJob import TestJob

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJob)
    unittest.TextTestRunner(verbosity=1).run(suite)
