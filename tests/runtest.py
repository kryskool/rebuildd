#!/usr/bin/env python2.5

import unittest
from TestJob import TestJob

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJob)
    unittest.TextTestRunner(verbosity=2).run(suite)
