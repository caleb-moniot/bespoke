"""
.. module:: hypervisor_test
   :platform: Linux, Windows
   :synopsis: Unit tests for hypervisor module. These tests are disabled by default.
   :license: BSD, see LICENSE for more details.

.. moduleauthor:: Ryan Gard <ryan.a.gard@outlook.com>
"""
__version__ = 0.1

#===================================================================================================
# Imports
#===================================================================================================
from unittest import TestCase, skip
from hypervisor import VBoxMachine
from time import sleep

#===================================================================================================
# Tests
#===================================================================================================
@skip('Skip non-portable tests! If you want to use these '
      'tests you must alter them for your environment!')
class VBoxMachineTests_Non_Portable(TestCase):
    """Happy path tests for the VBoxMachine class in the hypervisor module."""
    
    def setUp(self):
        self.test_vm = VBoxMachine('localhost', 'bespoke')
        sleep(5)
    
    def tearDown(self):
        sleep(5)
    
    def test1_start_vm(self):
        """Verify that a stopped VM can be started."""
        
        self.test_vm.start()
    
    def test2_restart_vm(self):
        """Verify that a running VM can be restarted."""
        
        self.test_vm.restart()
    
    def test3_stop_vm(self):
        """Verify that a running VM can be stopped."""
        
        self.test_vm.stop()
    
    def test4_apply_snapshot(self):
        """Verify that a snapshot can be applied to a powered off machine."""
        
        self.test_vm.apply_snapshot('Basic')
        