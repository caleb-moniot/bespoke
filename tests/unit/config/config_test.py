"""
.. module:: resource_config_mock_test
   :platform: Linux, Windows
   :synopsis: Unit tests for the config module.
   :license: BSD, see LICENSE for more details.

.. moduleauthor:: Ryan Gard <ryan.a.gard@outlook.com>
"""
__version__ = 0.1

#===================================================================================================
# Imports
#===================================================================================================
from unittest import TestCase, skipIf
from config import ResourceConfig, TestPlanConfig, ConfigError
from core import BasicInstaller, MSIInstaller
from mock import patch

#===================================================================================================
# Globals
#===================================================================================================
SKIP_EVERYTHING = False
SHARED_CONFIGS = r'../../shared_configs/'
BESPOKE_XSD = r'../../../src/bespoke/xsd/'

#===================================================================================================
# Classes
#===================================================================================================
class TestCaseStub(object):
    def __init__(self, name):
        self.name = name
    
    def add_test_prep(self, 
                      resource_id,
                      sut,
                      checkpoint,
                      tools,
                      builds,
                      agent_commands,
                      post_wait,
                      timeout,
                      restart,
                      restart_wait):
        pass
    
    def add_test_step(self, 
                      description, 
                      resource_id, 
                      test_directory,
                      interpreter,
                      test_exec,
                      test_params,
                      timeout, 
                      post_wait, 
                      restart, 
                      restart_wait):
        pass
    
    def add_build(self, sut, build, timeout):
        pass
    
    def add_tool(self, sut, tool, timeout):
        pass
    
    def add_resoure_refresh(self, resource_id):
        pass
    
    def execute(self):
        pass
    
class SystemUnderTestStub(object):
    def __init__(self, 
                 alias,
                 machine=None,
                 bespoke_root='/opt/bespoke',
                 credentials=None,
                 machine_type=None,
                 network_address=None,
                 os=None,
                 os_label=None,
                 arch_type=None,
                 role=None,
                 check_points=None,
                 tools=None):
        
        self._alias = alias
        self._machine = machine
        self._bespoke_root = bespoke_root
        self._credentials = credentials
        self._machine_type = machine_type
        self._network_address = network_address
        self._os = os
        self._os_label = os_label
        self._arch_type = arch_type
        self._role = role
        self._check_points = check_points
        self._available_tools = tools
        
    @property        
    def alias(self):
        return self._alias
    
    @property        
    def bespoke_root(self):
        return self._bespoke_root
        
class ToolStub(object):
    """Note: valid install types = basic_install, msi_install, no_install"""
    def __init__(self, 
                 name, 
                 install_type,
                 os_type=None,
                 os_arch=None,
                 version=None,
                 source_type=None, 
                 source_copy_once=None,
                 source_properties=None, 
                 install_properties=None):
        
        self._name = name
        self._os_type = os_type
        self._os_arch = os_arch
        self._version = version
        self._source_type = source_type
        self._source_copy_once = source_copy_once
        self._install_type = install_type
        self._source_properties = source_properties
        self._install_properties = install_properties
    
    @property
    def name(self):
        return self._name
    
    @property
    def install_type(self):
        return self._install_type
#===================================================================================================
# Mock-in Stubs
#===================================================================================================
def _add_virtual_machine_stub(self, content):
        """A stub method that stubs the internal 'content' dictionary for the 'Machine' key."""
        content['Machine'] = None

def _add_virtual_template_stub(self, content):
        """"A stub method that stubs the internal 'content' dictionary for the 'Machine' key."""
        content['Machine'] = None
        
#===================================================================================================
# Tests
#===================================================================================================
@patch.object(ResourceConfig, '_add_virtual_machine', new=_add_virtual_machine_stub)
@patch.object(ResourceConfig, '_add_virtual_template', new=_add_virtual_template_stub)
class ResourceConfigTests(TestCase):
    """Tests for the ResourceConfig class in the config module."""
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test1_happy_path_static(self):
        """Happy path test to verify static SystemUnderTest machines are handled correct. 
            * No tools
            * No checkpoints
        """
        
        test_config = ResourceConfig(SHARED_CONFIGS + r'resource/happy_path_static.xml',
                                     BESPOKE_XSD + r'resource_config.xsd')
        
        actual_vm_1 = test_config['BVT-2k8-R2-64']
        
        #VM1 Verification
        self.assertEqual(actual_vm_1.alias, 'BVT-2k8-R2-64')
        self.assertEqual(actual_vm_1.network_address, 'bvt-2k8-r2-64.fancylads.local')
        self.assertEqual(actual_vm_1.bespoke_root, r'C:\Bespoke\TestManager')
        self.assertEqual(actual_vm_1.machine_type, 'static')
        self.assertDictEqual(actual_vm_1.credentials, {r'FancyLads\BobTester':'password'})
        self.assertEqual(actual_vm_1.os, 'Windows')
        self.assertEqual(actual_vm_1.os_label, 'Windows 2008 R2')
        self.assertEqual(actual_vm_1.arch_type, 'x64')
        self.assertEqual(actual_vm_1.role, 'Server')
        self.assertEqual(len(actual_vm_1.check_points), 0)
        self.assertEqual(len(actual_vm_1.tools), 0)
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test2_reference_to_sut(self):
        """Verify that when using the dictionary "__getitem__" method for static VM machines that 
        we get a reference of the SystemUnderTest rather than a copy of the original in 
        the "_content" dictionary.
        """
        
        test_config = ResourceConfig(SHARED_CONFIGS + r'resource/happy_path_static.xml',
                                     BESPOKE_XSD + r'resource_config.xsd')
        
        actual_template_1 = test_config['BVT-2k8-R2-64']
        
        self.assertIs(actual_template_1, test_config._content['BVT-2k8-R2-64'])
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test3_tools(self):
        """Happy path test to verify static SystemUnderTest machines are handled correct. 
            * Tools
            * No checkpoints
        """
        
        test_config = ResourceConfig(SHARED_CONFIGS + r'resource/tools_static.xml',
                                     BESPOKE_XSD + r'resource_config.xsd')
        
        #Expected tools
        exp_tools = ['BillyMcToolin', 'ToolMeFaceHole', 'ThoughtBadger']
        
        actual_vm_1 = test_config['BVT-2k8-R2-64']
        
        #VM1 Verification
        self.assertEqual(actual_vm_1.alias, 'BVT-2k8-R2-64')
        self.assertEqual(actual_vm_1.network_address, 'bvt-2k8-r2-64.fancylads.local')
        self.assertEqual(actual_vm_1.bespoke_root, r'C:\Bespoke\TestManager')
        self.assertEqual(actual_vm_1.machine_type, 'static')
        self.assertDictEqual(actual_vm_1.credentials, {r'FancyLads\BobTester':'password'})
        self.assertEqual(actual_vm_1.os, 'Windows')
        self.assertEqual(actual_vm_1.os_label, 'Windows 2008 R2')
        self.assertEqual(actual_vm_1.arch_type, 'x64')
        self.assertEqual(actual_vm_1.role, 'Server')
        self.assertEqual(len(actual_vm_1.check_points), 0)
        self.assertListEqual(actual_vm_1.tools, exp_tools)
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test4_tools_checkpoints(self):
        """Happy path test to verify static SystemUnderTest machines are handled correct. 
            * Tools
            * Checkpoints
        """
        
        test_config = ResourceConfig(SHARED_CONFIGS + r'resource/checkpoints_static.xml',
                                     BESPOKE_XSD + r'resource_config.xsd')
        
        #Expected tools
        exp_tools = ['BillyMcToolin', 'ToolMeFaceHole', 'ThoughtBadger']
        
        #Expected checkpoints.
        exp_checkpoints = {'Test': [], 'TestLess': [], 'TestMore': []}
        
        actual_vm_1 = test_config['BVT-2k8-R2-64']
        
        #VM1 Verification
        self.assertEqual(actual_vm_1.alias, 'BVT-2k8-R2-64')
        self.assertEqual(actual_vm_1.network_address, 'bvt-2k8-r2-64.fancylads.local')
        self.assertEqual(actual_vm_1.bespoke_root, r'C:\Bespoke\TestManager')
        self.assertEqual(actual_vm_1.machine_type, 'static')
        self.assertDictEqual(actual_vm_1.credentials, {r'FancyLads\BobTester':'password'})
        self.assertEqual(actual_vm_1.os, 'Windows')
        self.assertEqual(actual_vm_1.os_label, 'Windows 2008 R2')
        self.assertEqual(actual_vm_1.arch_type, 'x64')
        self.assertEqual(actual_vm_1.role, 'Server')
        self.assertDictEqual(actual_vm_1.check_points, exp_checkpoints)
        self.assertListEqual(actual_vm_1.tools, exp_tools)
        
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test5_tools_checkpoints_with_tools(self):
        """Happy path test to verify static SystemUnderTest machines are handled correct. 
            * Tools
            * Checkpoints with tools.
        """
        
        test_config = ResourceConfig(SHARED_CONFIGS + r'resource/checkpoints_with_tools_static.xml',
                                     BESPOKE_XSD + r'resource_config.xsd')
        
        #Expected tools
        exp_tools = ['BillyMcToolin', 'ToolMeFaceHole', 'ThoughtBadger']
        
        #Expected checkpoints.
        exp_checkpoints = {'Test': ['CrazyPeople'],
                           'TestLess': ['ExtremeKnitting', 'PowerfulManThighs', 'GiantWomanFeet'],
                           'TestMore': ['DumbThings', 'DumberThings']}
        
        actual_vm_1 = test_config['BVT-2k8-R2-64']
        
        #VM1 Verification
        self.assertEqual(actual_vm_1.alias, 'BVT-2k8-R2-64')
        self.assertEqual(actual_vm_1.network_address, 'bvt-2k8-r2-64.fancylads.local')
        self.assertEqual(actual_vm_1.bespoke_root, r'C:\Bespoke\TestManager')
        self.assertEqual(actual_vm_1.machine_type, 'static')
        self.assertDictEqual(actual_vm_1.credentials, {r'FancyLads\BobTester':'password'})
        self.assertEqual(actual_vm_1.os, 'Windows')
        self.assertEqual(actual_vm_1.os_label, 'Windows 2008 R2')
        self.assertEqual(actual_vm_1.arch_type, 'x64')
        self.assertEqual(actual_vm_1.role, 'Server')
        self.assertDictEqual(actual_vm_1.check_points, exp_checkpoints)
        self.assertListEqual(actual_vm_1.tools, exp_tools)
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test6_duplicate_alias_static(self):
        """Verify that we catch duplicate resource alias found in static VM machines."""
        
        #Attempt to checkout again.
        with self.assertRaises(ConfigError) as cm:
            ResourceConfig(SHARED_CONFIGS + r'resource/duplicate_alias_static.xml',
                           BESPOKE_XSD + r'resource_config.xsd')
            
        excep = cm.exception
        
        self.assertEqual(excep.msg, "The resource alias 'BVT-2k8-R2-64' used more than once!")
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test7_duplicate_alias_template(self):
        """Verify that we catch duplicate resource alias found in template VM machines."""
        
        #Attempt to checkout again.
        with self.assertRaises(ConfigError) as cm:
            ResourceConfig(SHARED_CONFIGS + r'resource/duplicate_alias_template.xml',
                           BESPOKE_XSD + r'resource_config.xsd')
            
        excep = cm.exception
        
        self.assertEqual(excep.msg, "The resource alias 'BVT-2k3-R2-32' used more than once!")
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test8_duplicate_alias_mixed(self):
        """Verify that we catch duplicate resource alias found in either template or static
        VM machines.
        """
        
        #Attempt to checkout again.
        with self.assertRaises(ConfigError) as cm:
            ResourceConfig(SHARED_CONFIGS + r'resource/duplicate_alias_mixed.xml',
                           BESPOKE_XSD + r'resource_config.xsd')
            
        excep = cm.exception
        
        self.assertEqual(excep.msg, "The resource alias 'BVT-2k8-R2-64' used more than once!")
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test9_happy_path_template(self):
        """Happy path test to verify templated SystemUnderTest machines are handled correct. 
            * No tools
        """
        
        test_config = ResourceConfig(SHARED_CONFIGS + r'resource/happy_path_template.xml',
                                     BESPOKE_XSD + r'resource_config.xsd')
        
        actual_template_1 = test_config['BVT-2k3-R2-32']
        
        #VM1 Verification
        self.assertEqual(actual_template_1.alias, 'BVT-2k3-R2-32')
        self.assertEqual(actual_template_1.bespoke_root, r'C:\Bespoke\TestManager')
        self.assertEqual(actual_template_1.machine_type, 'template')
        self.assertDictEqual(actual_template_1.credentials, {r'FancyLads\BobTester':'password'})
        self.assertEqual(actual_template_1.os, 'Windows')
        self.assertEqual(actual_template_1.os_label, 'Windows 2003 R2')
        self.assertEqual(actual_template_1.arch_type, 'x86')
        self.assertEqual(actual_template_1.role, 'Server')
        self.assertEqual(len(actual_template_1.tools), 0)
        
        #This information is not set by default for templates.
        self.assertEqual(actual_template_1.check_points, None)
        self.assertEqual(actual_template_1.network_address, None)
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test10_copy_of_sut(self):
        """Verify that when using the dictionary "__getitem__" method for templated VM machines that 
        we get a copy of the SystemUnderTest rather than a reference to the original in 
        the "_content" dictionary.
        """
        
        test_config = ResourceConfig(SHARED_CONFIGS + r'resource/happy_path_template.xml',
                                     BESPOKE_XSD + r'resource_config.xsd')
        
        actual_template_1 = test_config['BVT-2k3-R2-32']
        
        self.assertIsNot(actual_template_1, test_config._content['BVT-2k3-R2-32'])
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test11_tools(self):
        """Happy path test to verify templated SystemUnderTest machines are handled correct. 
            * Tools
        """
        
        test_config = ResourceConfig(SHARED_CONFIGS + r'resource/tools_template.xml',
                                     BESPOKE_XSD + r'resource_config.xsd')
        
        #Expected tools
        exp_tools = ['BillyMcToolin', 'ToolMeFaceHole', 'ThoughtBadger']
        
        actual_template_1 = test_config['BVT-2k3-R2-32']
        
        #VM1 Verification
        self.assertEqual(actual_template_1.alias, 'BVT-2k3-R2-32')
        self.assertEqual(actual_template_1.bespoke_root, r'C:\Bespoke\TestManager')
        self.assertEqual(actual_template_1.machine_type, 'template')
        self.assertDictEqual(actual_template_1.credentials, {r'FancyLads\BobTester':'password'})
        self.assertEqual(actual_template_1.os, 'Windows')
        self.assertEqual(actual_template_1.os_label, 'Windows 2003 R2')
        self.assertEqual(actual_template_1.arch_type, 'x86')
        self.assertEqual(actual_template_1.role, 'Server')
        self.assertListEqual(actual_template_1.tools, exp_tools)
        
        #This information is not set by default for templates.
        self.assertEqual(actual_template_1.check_points, None)
        self.assertEqual(actual_template_1.network_address, None)
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test12_missing_ext_config(self):
        """Verify that missing extended configuration elements generate appropriate exceptions.
        """
        
        #Attempt to checkout again.
        with self.assertRaises(ConfigError) as cm:
            ResourceConfig(SHARED_CONFIGS + r'resource/missing_ext_config_template.xml',
                           BESPOKE_XSD + r'resource_config.xsd')
            
        excep = cm.exception
        
        self.assertEqual(excep.msg, 'The extended config element "VagrantHypervisor" is required '
                                    'for the Vagrant template "BVT-2k3-R2-32"!')
        
class TestPlanConfigTests(TestCase):
    """Tests for the TestPlanConfig class in the config module."""
    
    def setUp(self):        
        self.builds = {'Happy_Build':ToolStub('Happy_Build', 'msi_install'),
                       'Unhappy_Build':ToolStub('Unhappy_Build', 'no_install'),
                       'Mildly_Happy_Build':ToolStub('Mildly_Happy_Build', 'basic_install')}
        self.tools = {'Tool_1':ToolStub('Tool_1', 'msi_install'),
                      'Tool_2':ToolStub('Tool_2', 'basic_install'),
                      'Tool_3':ToolStub('Tool_3', 'msi_install')}
        self.resources = {'Windows_VM':SystemUnderTestStub('Windows_VM'),
                          'CentOS_VM':SystemUnderTestStub('CentOS_VM'),
                          'Ubuntu_VM':SystemUnderTestStub('Ubuntu_VM')}
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test1_happy_path_resource_count(self):
        """Verify that the number of elements is correct in the test case.."""
        
        test_config = TestPlanConfig(SHARED_CONFIGS + r'test_plan/happy_path.xml',
                                     BESPOKE_XSD + r'test_plan.xsd',
                                     self.builds,
                                     self.tools,
                                     self.resources)
        
        #Items returns a tuple of key|value pair hence the 2 order array syntax.
        self.assertEqual(len(test_config['Happy_Test_Case_1']._tests), 
                         19, 
                         'Incorrect number of elements found in TestCase!')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test2_happy_path_test_prep(self):
        """Verify that the "TestPrep" elements exist in the right order with the correct
        content."""
        
        test_config = TestPlanConfig(SHARED_CONFIGS + r'test_plan/happy_path.xml',
                                     BESPOKE_XSD + r'test_plan.xsd',
                                     self.builds,
                                     self.tools,
                                     self.resources)
        #Element 0
        test_prep_0 = test_config['Happy_Test_Case_1']._tests[0]
        self.assertEqual(test_prep_0.name, 'Test_System_1', 'Incorrect TestPrep name!')
        self.assertEqual(test_prep_0.sut.alias, 'Windows_VM', 'Incorrect SUT name!')
        self.assertEqual(test_prep_0._checkpoint, 'ReadyToAutoTest', 'Incorrect checkpoint!')
        self.assertEqual(test_prep_0._post_wait, 5, 'Incorrect postwait!')
        self.assertEqual(test_prep_0._timeout, 600, 'Incorrect timeout!')
        
        #Element 5
        test_prep_5 = test_config['Happy_Test_Case_1']._tests[5]
        self.assertEqual(test_prep_5.name, 'Test_System_2', 'Incorrect TestPrep name!')
        self.assertEqual(test_prep_5.sut.alias, 'CentOS_VM', 'Incorrect SUT name!')
        self.assertEqual(test_prep_5._checkpoint, 'StartTesting', 'Incorrect checkpoint!')
        self.assertEqual(test_prep_5._post_wait, 8, 'Incorrect postwait!')
        self.assertEqual(test_prep_5._timeout, 599, 'Incorrect timeout!')
        
        #Element 8
        test_prep_8 = test_config['Happy_Test_Case_1']._tests[8]
        self.assertEqual(test_prep_8.name, 'Test_System_3', 'Incorrect TestPrep name!')
        self.assertEqual(test_prep_8.sut.alias, 'Ubuntu_VM', 'Incorrect SUT name!')
        self.assertEqual(test_prep_8._checkpoint, 'TestNow', 'Incorrect checkpoint!')
        self.assertEqual(test_prep_8._post_wait, 123124, 'Incorrect postwait!')
        self.assertEqual(test_prep_8._timeout, 2, 'Incorrect timeout!')
        
        #Element 12
        test_prep_12 = test_config['Happy_Test_Case_1']._tests[12]
        self.assertEqual(test_prep_12.name, 'Test_System_1', 'Incorrect TestPrep name!')
        self.assertEqual(test_prep_12.sut.alias, 'Windows_VM', 'Incorrect SUT name!')
        self.assertEqual(test_prep_12._checkpoint, 'ReadyToAutoTest', 'Incorrect checkpoint!')
        self.assertEqual(test_prep_12._post_wait, 5, 'Incorrect postwait!')
        self.assertEqual(test_prep_12._timeout, 600, 'Incorrect timeout!')
        
        #Element 15
        test_prep_15 = test_config['Happy_Test_Case_1']._tests[5]
        self.assertEqual(test_prep_15.name, 'Test_System_2', 'Incorrect TestPrep name!')
        self.assertEqual(test_prep_15.sut.alias, 'CentOS_VM', 'Incorrect SUT name!')
        self.assertEqual(test_prep_15._checkpoint, 'StartTesting', 'Incorrect checkpoint!')
        self.assertEqual(test_prep_15._post_wait, 8, 'Incorrect postwait!')
        self.assertEqual(test_prep_15._timeout, 599, 'Incorrect timeout!')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test3_happy_path_test_installers(self):
        """Verify that the "_Installer" elements exist in the right order with the correct
        content."""
        
        test_config = TestPlanConfig(SHARED_CONFIGS + r'test_plan/happy_path.xml',
                                     BESPOKE_XSD + r'test_plan.xsd',
                                     self.builds,
                                     self.tools,
                                     self.resources)
        
        #Element 2
        test_installer_2 = test_config['Happy_Test_Case_1']._tests[2]
        self.assertEqual(test_installer_2._tool.name, 'Tool_1', 'Incorrect tool name!')
        self.assertIsInstance(test_installer_2, MSIInstaller, 'Incorrect installer type!')
        
        #Element 3
        test_installer_3 = test_config['Happy_Test_Case_1']._tests[3]
        self.assertEqual(test_installer_3._tool.name, 'Tool_2', 'Incorrect tool name!')
        self.assertIsInstance(test_installer_3, BasicInstaller, 'Incorrect installer type!')
        
        #Element 4
        test_installer_4 = test_config['Happy_Test_Case_1']._tests[4]
        self.assertEqual(test_installer_4._tool.name, 'Happy_Build', 'Incorrect tool name!')
        self.assertIsInstance(test_installer_4, MSIInstaller, 'Incorrect installer type!')
        
        #Element 7
        test_installer_7 = test_config['Happy_Test_Case_1']._tests[7]
        self.assertEqual(test_installer_7._tool.name, 'Tool_2', 'Incorrect tool name!')
        self.assertIsInstance(test_installer_7, BasicInstaller, 'Incorrect installer type!')
        
        #Element 9
        test_installer_9 = test_config['Happy_Test_Case_1']._tests[9]
        self.assertEqual(test_installer_9._tool.name, 'Tool_3', 'Incorrect tool name!')
        self.assertIsInstance(test_installer_9, MSIInstaller, 'Incorrect installer type!')
        
        #Element 10
        test_installer_10 = test_config['Happy_Test_Case_1']._tests[10]
        self.assertEqual(test_installer_10._tool.name, 'Mildly_Happy_Build', 'Incorrect tool name!')
        self.assertIsInstance(test_installer_10, BasicInstaller, 'Incorrect installer type!')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test4_happy_path_test_power_control(self):
        """Verify that the "PowerControl" elements exist in the right order with the correct
        content."""
        
        test_config = TestPlanConfig(SHARED_CONFIGS + r'test_plan/happy_path.xml',
                                     BESPOKE_XSD + r'test_plan.xsd',
                                     self.builds,
                                     self.tools,
                                     self.resources)
        
        #Element 1
        test_power_control_1 = test_config['Happy_Test_Case_1']._tests[1]
        self.assertEqual(test_power_control_1.name, 
                         'Test_System_1_PowerControl', 
                         'Incorrect power control name!')
        self.assertTrue(test_power_control_1._wait, 'Incorrect wait status!')
        
        #Element 6
        test_power_control_6 = test_config['Happy_Test_Case_1']._tests[6]
        self.assertEqual(test_power_control_6.name, 
                         'Test_System_2_PowerControl', 
                         'Incorrect power control name!')
        self.assertFalse(test_power_control_6._wait, 'Incorrect wait status!')
        
        #Element 13
        test_power_control_13 = test_config['Happy_Test_Case_1']._tests[13]
        self.assertEqual(test_power_control_13.name, 
                         'Test_System_1_PowerControl', 
                         'Incorrect power control name!')
        self.assertTrue(test_power_control_13._wait, 'Incorrect wait status!')
        
        #Element 16
        test_power_control_16 = test_config['Happy_Test_Case_1']._tests[16]
        self.assertEqual(test_power_control_16.name, 
                         'Test_System_2_PowerControl', 
                         'Incorrect power control name!')
        self.assertFalse(test_power_control_16._wait, 'Incorrect wait status!')
        
        #Element 18
        test_power_control_18 = test_config['Happy_Test_Case_1']._tests[18]
        self.assertEqual(test_power_control_18.name, 
                         'Test Step 3_PowerControl', 
                         'Incorrect power control name!')
        self.assertTrue(test_power_control_18._wait, 'Incorrect wait status!')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test5_happy_path_test_steps(self):
        """Verify that the "Step" elements exist in the right order with the correct
        content."""
        
        test_config = TestPlanConfig(SHARED_CONFIGS + r'test_plan/happy_path.xml',
                                     BESPOKE_XSD + r'test_plan.xsd',
                                     self.builds,
                                     self.tools,
                                     self.resources)
        
        #Element 11
        test_step_11 = test_config['Happy_Test_Case_1']._tests[11]
        self.assertEqual(test_step_11.name, 'Test Step 1', 'Incorrect step name!')
        self.assertEqual(test_step_11._sut.alias, 'Windows_VM', 'Incorrect SUT!')
        self.assertEqual(test_step_11._interpreter, None, 'Incorrect interpreter!')
        self.assertEqual(test_step_11._post_wait, 5, 'Incorrect postwait!')
        self.assertEqual(test_step_11._test_directory, 
                         'Fancy_Lads\\Tests', 
                         'Incorrect test directory!')
        self.assertEqual(test_step_11._test_exec, 'happy_tester.exe', 'Incorrect test exec!')
        self.assertEqual(test_step_11.timeout, 600, 'Incorrect timeout')
        self.assertDictEqual(test_step_11._test_params, 
                             {'--cwd': '"\\"C:\\tests\\""', '--resultsPath': '"\\"C:\\temp\\""'},
                             'Incorrect params!')
        
        #Element 14
        test_step_14 = test_config['Happy_Test_Case_1']._tests[14]
        self.assertEqual(test_step_14.name, 'Test Step 2', 'Incorrect step name!')
        self.assertEqual(test_step_14._sut.alias, 'CentOS_VM', 'Incorrect SUT!')
        self.assertEqual(test_step_14._interpreter, 'python', 'Incorrect interpreter!')
        self.assertEqual(test_step_14._post_wait, 10, 'Incorrect postwait!')
        self.assertEqual(test_step_14._test_directory, 
                         'Fancy_Lads\\More_Tests', 
                         'Incorrect test directory!')
        self.assertEqual(test_step_14._test_exec, 'super_happy_tester.py', 'Incorrect test exec!')
        self.assertEqual(test_step_14.timeout, 6000, 'Incorrect test timeout!')
        self.assertDictEqual(test_step_14._test_params, 
                             {'--cwd': '"\\"C:\\tests\\""', '--resultsPath': '"\\"C:\\happy\\""'},
                             'Incorrect params!')
        
        #Element 17
        test_step_17 = test_config['Happy_Test_Case_1']._tests[17]
        self.assertEqual(test_step_17.name, 'Test Step 3', 'Incorrect step name!')
        self.assertEqual(test_step_17._sut.alias, 'Ubuntu_VM', 'Incorrect SUT!')
        self.assertEqual(test_step_17._interpreter, 'perl', 'Incorrect interpreter!')
        self.assertEqual(test_step_17._post_wait, 7, 'Incorrect postwait!')
        self.assertEqual(test_step_17._test_directory, 
                         'Fancy_Lads\\Even_More_Tests', 
                         'Incorrect test directory!')
        self.assertEqual(test_step_17._test_exec, 'sad_tester.pl', 'Incorrect test exec!')
        self.assertEqual(test_step_17.timeout, 333, 'Incorrect test timeout!')
        self.assertDictEqual(test_step_17._test_params, 
                             {'--cwd': '"\\"C:\\unhappy_tests\\""', '--resultsPath': '"\\"C:\\sad\\""'},
                             'Incorrect params!')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test6_bad_build(self):
        """Verify that the user can't specify builds that don't exist."""
            
        #Attempt to open a config with a bad build.
        with self.assertRaises(ConfigError) as cm:
            TestPlanConfig(SHARED_CONFIGS + r'test_plan/bad_build.xml',
                           BESPOKE_XSD + r'test_plan.xsd',
                           self.builds,
                           self.tools,
                           self.resources)
            
        excep = cm.exception
        
        self.assertEqual(excep.msg, 'The build "Bad_Build" specified in the "Bad_Build_Test_Case" '
                                    'test case not defined in any BuildConfig!') 
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test7_duplicate_builds(self):
        """Verify that the user can't specify the same build twice."""
        
        #Attempt to open a config with the same build specified twice.
        with self.assertRaises(ConfigError) as cm:
            TestPlanConfig(SHARED_CONFIGS + r'test_plan/duplicate_builds.xml',
                           BESPOKE_XSD + r'test_plan.xsd',
                           self.builds,
                           self.tools,
                           self.resources)
            
        excep = cm.exception
        
        self.assertEqual(excep.msg, 'The build "Happy_Build" used more than once in the '
                                    '"Duplicate_Build_Test_Case" test case!')
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test8_bad_tool(self):
        """Verify that the user can't specify tools that don't exist."""
        
        #Attempt to open a config with the same build specified twice.
        with self.assertRaises(ConfigError) as cm:
            TestPlanConfig(SHARED_CONFIGS + r'test_plan/bad_tool.xml',
                           BESPOKE_XSD + r'test_plan.xsd',
                           self.builds,
                           self.tools,
                           self.resources)
            
        excep = cm.exception
        
        self.assertEqual(excep.msg, 'The tool "Bad_Tool" specified in the "Bad_Tool_Test_Case" '
                                    'test case not defined in any ToolConfig!')
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test9_duplicate_tools(self):
        """Verify that the user can't specify the same tool twice."""
        
        #Attempt to open a config with the same tool specified twice.
        with self.assertRaises(ConfigError) as cm:
            TestPlanConfig(SHARED_CONFIGS + r'test_plan/duplicate_tools.xml',
                           BESPOKE_XSD + r'test_plan.xsd',
                           self.builds,
                           self.tools,
                           self.resources)
            
        excep = cm.exception
        
        self.assertEqual(excep.msg, 'The tool "Tool_1" used more than once in the '
                                    '"Duplicate_Tool_Test_Case" test case!')
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test10_invalid_test_exe(self):
        """Verify that invalid test executable is recognized and rejected."""
        
        #Attempt to open a config with invalid executable in test step.
        with self.assertRaises(ConfigError) as cm:
            TestPlanConfig(SHARED_CONFIGS + r'test_plan/invalid_executable.xml',
                           BESPOKE_XSD + r'test_plan.xsd',
                           self.builds,
                           self.tools,
                           self.resources)
            
        excep = cm.exception
        
        self.assertEqual(excep.msg, "Element 'Executable': '' is not a valid value of the atomic "
                                    "type 'nonEmptyString'. Line: 23 Column: 0")
        