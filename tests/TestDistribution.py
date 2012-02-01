#!/usr/bin/python
import sys  
  
sys.path.insert(0, "..")  
sys.path.insert(0, ".")  

from RebuilddTestSetup import rebuildd_global_test_setup, rebuildd_global_test_teardown
import unittest, types, os
from rebuildd.Distribution import Distribution
from rebuildd.RebuilddConfig import RebuilddConfig
from rebuildd.Rebuildd import Rebuildd
from rebuildd.Package import Package

class TestDistribution(unittest.TestCase):

    def setUp(self):
        rebuildd_global_test_setup()
        self.d = Distribution("sid", "alpha")
        self.package = Package(name="xutils", version="7.1.ds.3-1")
        self.package_dotted = Package(name="xutils", version="1:7.1.ds.3-1")

    def tearDown(self):
        rebuildd_global_test_teardown()

    def test_name(self):
        self.assert_(self.d.name is "sid")

    def test_arch(self):
        self.assert_(self.d.arch is "alpha")
                
    def test_get_source_cmd(self):
        RebuilddConfig().set('build', 'source_cmd', '/bin/true $d $a $p $v')
        cmd = self.d.get_source_cmd(self.package)
        self.assert_(self.d.name in cmd)
        self.assert_(self.package.name in cmd)
        self.assert_(self.package.version in cmd)

    def test_get_build_cmd(self):
        RebuilddConfig().set('build', 'build_cmd', '/bin/true $d $a $p $v')
        cmd = self.d.get_build_cmd(self.package)
        self.assert_(self.d.name in cmd)
        self.assert_(self.d.arch in cmd)
        self.assert_(self.package.name in cmd)
        self.assert_(self.package.version in cmd)
        cmd = self.d.get_build_cmd(self.package_dotted)
        self.assert_(self.package_dotted.version not in cmd)

    def test_get_post_build_cmd(self):
        RebuilddConfig().set('build', 'post_build_cmd', '')
        cmd = self.d.get_post_build_cmd(self.package)
        self.assert_(cmd is None)
        RebuilddConfig().set('build', 'post_build_cmd', '/bin/true $d $a $p $v')
        cmd = self.d.get_post_build_cmd(self.package)
        self.assert_(self.d.name in cmd)
        self.assert_(self.package.name in cmd)
        self.assert_(self.package.version in cmd)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDistribution)
    unittest.TextTestRunner(verbosity=2).run(suite)
