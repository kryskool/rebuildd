#!/usr/bin/env python2.5
import sys  
  
sys.path.insert(0, "..")  
sys.path.insert(0, ".")  

from RebuilddTestSetup import rebuildd_global_test_setup
import unittest, types, os
from rebuildd.Distribution import Distribution
from rebuildd.RebuilddConfig import RebuilddConfig
from rebuildd.Rebuildd import Rebuildd
from rebuildd.Package import Package

class TestDistribution(unittest.TestCase):

    def setUp(self):
        rebuildd_global_test_setup()
        self.d = Distribution("sid")
        self.package = Package(name="zsh", version="4.3.4-10")

    def test_name(self):
        self.assert_(self.d.name is "sid")
                
    def test_get_source_cmd(self):
        cmd = self.d.get_source_cmd(self.package)
        self.assert_(self.d.name in cmd)
        self.assert_(self.package.name in cmd)
        self.assert_(self.package.version in cmd)

    def test_get_build_cmd(self):
        cmd = self.d.get_build_cmd(self.package)
        self.assert_(self.d.name in cmd)
        self.assert_(self.package.name in cmd)
        self.assert_(self.package.version in cmd)

    def test_get_post_build_cmd(self):
        RebuilddConfig().set('build', 'post_build_cmd', '')
        cmd = self.d.get_post_build_cmd(self.package)
        self.assert_(cmd is None)
        RebuilddConfig().set('build', 'post_build_cmd', '/bin/true %s %s %s')
        cmd = self.d.get_post_build_cmd(self.package)
        self.assert_(self.d.name in cmd)
        self.assert_(self.package.name in cmd)
        self.assert_(self.package.version in cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDistribution)
    unittest.TextTestRunner(verbosity=2).run(suite)
