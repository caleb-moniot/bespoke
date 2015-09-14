"""
.. module:: config_test
   :platform: Linux, Windows
   :synopsis: Unit tests for the config module.
   :license: BSD, see LICENSE for more details.

.. moduleauthor:: Ryan Gard <ryan.a.gard@outlook.com>
"""
__version__ = 0.2

#===================================================================================================
# Imports
#===================================================================================================
from unittest import TestCase, skipIf
from config import _Config, GlobalConfig, ToolConfig, BuildConfig, TestRunConfig, ConfigError

#===================================================================================================
# Globals
#===================================================================================================
SKIP_EVERYTHING = False
SHARED_CONFIGS = r'../../shared_configs/'
BESPOKE_XSD = r'../../../src/bespoke/xsd/'

#===================================================================================================
# Classes
#===================================================================================================
class _ConfigAccessor(_Config):
    """Since _Config is an AbstractBaseClass with methods and properties that must be overridden 
    we have to create a subclass that does the bare minimum overrides to test the class indirectly.
    
    Args:
        xml_config_path (str): The path to the XML config file that contains
            information to be parsed and stored.
        _xsd_file (str)(opt): The path to the XSD file to use for XML 
            validation.
        
    Raises:
        :class:`ConfigError`: The config file or XSD file were not found.
    """
    
    def __init__(self, xml_config_path, xsd_file=''):
        super(_ConfigAccessor, self).__init__(xml_config_path, xsd_file)
    
    def __getitem__(self, key):
        super(_ConfigAccessor, self).__getitem__(key)
        
    def __iter__(self):
        super(_ConfigAccessor, self).__iter__()
        
    def load_content(self):
        pass
    
    def _load_xsd(self):
        super(_ConfigAccessor, self)._load_xsd()
        
    def validate_config(self, suppress_exceptions=False):
        super(_ConfigAccessor, self).validate_config(suppress_exceptions)
    
    def parse_config(self, validate=True):
        super(_ConfigAccessor, self).parse_config(validate)
        
#===================================================================================================
# Tests
#===================================================================================================
class _ConfigTests(TestCase):
    """This class contains all the tests for the base _Config class.
    """

    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test1_happy_path(self):
        """This test will verify that a valid config will validate against a valid xsd."""
        
        test_obj = _ConfigAccessor(SHARED_CONFIGS + r'_config/happy_path.xml',
                                   SHARED_CONFIGS + r'_config/happy_path.xsd')
        
        test_obj.parse_config()
        
        self.assertIsInstance(test_obj, _Config)
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test2_incorrect_xsd_path(self):
        """This test will verify that the _Config class handles a bogus XSD path correctly."""
        
        with self.assertRaises(ConfigError) as cm:
            _ConfigAccessor(SHARED_CONFIGS + r'_config/happy_path.xml',
                            r'bogus_path_to.xsd')
             
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, 'XSD file not found!')
        self.assertEqual(excep._config_file, 'bogus_path_to.xsd')
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test3_incorrect_xml_path(self):
        """This test will verify that the _Config class handles a bogus XML path correctly."""
        
        with self.assertRaises(ConfigError) as cm:
            _ConfigAccessor(r'this_file_is_not_here.xml', 
                            SHARED_CONFIGS + r'_config/happy_path.xsd')
             
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, 'Config file not found!')
        self.assertEqual(excep._config_file, 'this_file_is_not_here.xml')
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test4_load_xsd_broken_xml(self):
        """This test will verify that the '_load_xsd' method will handle broken XML correctly."""
        
        test_obj = _ConfigAccessor(SHARED_CONFIGS + r'_config/happy_path.xml',
                                   SHARED_CONFIGS + r'_config/broken.xsd')
        
        with self.assertRaises(ConfigError) as cm:
            test_obj._load_xsd()
             
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, 'error parsing attribute name, line 27, column 1')
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'_config/broken.xsd')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test5_load_xsd_invalid(self):
        """This test will verify that the '_load_xsd' method will handle invalid XMLSchema."""
        test_obj = _ConfigAccessor(SHARED_CONFIGS + r'_config/happy_path.xml',
                                   SHARED_CONFIGS + r'_config/invalid.xsd')
        
        with self.assertRaises(ConfigError) as cm:
            test_obj._load_xsd()
             
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, 
                        ("element decl. 'Path', attribute 'type': The QName "
                         "value 'validFilePath' does not resolve to a(n) type "
                         "definition., line 18"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'_config/invalid.xsd')
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test6_validate_invalid_config(self):
        """This test will verify that the 'validate_config' method will handle invalid XML 
        documents. (The document is proper XML, but violates the schema in some way.)
        """
        
        test_obj = _ConfigAccessor(SHARED_CONFIGS + r'_config/invalid_config.xml',
                                   SHARED_CONFIGS + r'_config/happy_path.xsd')
        
        #Parse the doc without validation.
        test_obj.parse_config(validate=False)
        
        with self.assertRaises(ConfigError) as cm:
            test_obj.validate_config()
             
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, 
                        ("Element 'NotAllowed': This element is not expected. "
                         "Expected is one of ( Stuff, Numbers, ComplexStuff ). "
                         "Line: 9 Column: 0"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'_config/invalid_config.xml')
        
        #Verify that we can also suppress the exceptions.
        self.assertFalse(test_obj.validate_config(suppress_exceptions=True))
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test7_parse_broken_config(self):
        """This test will verify that a valid config will validate against a valid xsd."""
        
        test_obj = _ConfigAccessor(SHARED_CONFIGS + r'_config/broken_config.xml',
                                   SHARED_CONFIGS + r'_config/happy_path.xsd')
        
        with self.assertRaises(ConfigError) as cm:
            test_obj.parse_config()
             
        #Verify exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, 
                        "StartTag: invalid element name, line 9, column 4")
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'_config/broken_config.xml')
        
        #Verify that an ConfigError is raised if validation is attempted on a
        #non-parsed config file.
        with self.assertRaises(ConfigError) as cm:
            test_obj.validate_config()
        
        #Verify exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, 
                        ("The config has not been parsed yet! You must run "
                         "'parse_config' before validating!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'_config/broken_config.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test8_missing_config_version(self):
        """This test will verify that a valid config will validate against a valid xsd."""
        
        test_obj = _ConfigAccessor(SHARED_CONFIGS + r'_config/missing_config_version.xml',
                                   SHARED_CONFIGS + r'_config/happy_path.xsd')
        
        with self.assertRaises(ConfigError) as cm:
            test_obj.parse_config()
             
        #Verify exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, 
                        ("Root element of config file is missing the mandatory "
                         "attribute 'version'!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'_config/missing_config_version.xml')
        
class GlobalConfigTests(TestCase):
    """Tests for the GlobalConfig class in the config module."""
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test1_happy_path(self):
        """Happy path test to verify that the GlobalConfig class works."""
        
        dicTest = {'BespokeServerHostname':'Grim',
                   'ConfigPath':'configs',
                   'TestRunPath':'testruns',
                   'TestPlanPath':'testplans',
                   'TestScriptPath':'testscripts',
                   'ToolPath':'tools',
                   'ResultsPath':'results',
                   'ResultsURL':r'\\ryan-pc.bespoke.com\bespoke',
                   'GlobalLog':'bespoke_trace.log',
                   'ResourceConfigs':['ResourceConfig.xml']}
        
        cfgTest = GlobalConfig(SHARED_CONFIGS + r'global/happy_path.xml', BESPOKE_XSD + r'/global_config.xsd')
        
        self.assertEqual(cfgTest._content, dicTest)
        self.assertEqual(cfgTest._config_version, 3)

class ToolConfigTests(TestCase):
    """Tests for the ToolConfig class in the config module."""
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test1_happy_path(self):
        """Happy path test to verify that the ToolConfig class works."""
        
        test_config = ToolConfig(SHARED_CONFIGS + r'tools/happy_path.xml',
                                 BESPOKE_XSD + r'/tool_config.xsd',
                                 r'Tool')
        
        actual_monocle_tool = test_config['Monocle']
        actual_tailor_tool = test_config['Tailor']
        actual_top_hat_tool = test_config['Top Hat']
        actual_cobbler_tool = test_config['Cobbler']
        
        #Monocle Tool Verification
        self.assertEqual(actual_monocle_tool.name, 'Monocle')
        self.assertEqual(actual_monocle_tool.os_type, 'Windows')
        self.assertEqual(actual_monocle_tool.os_arch, 'x64')
        self.assertEqual(actual_monocle_tool.version, '1.0.1')
        self.assertEqual(actual_monocle_tool.source_copy_once, True)
        self.assertEqual(actual_monocle_tool.source_type, 'basic_copy')
        self.assertEqual(actual_monocle_tool.install_type, 'basic_install')
        self.assertEqual(actual_monocle_tool.source_properties['source_path'], 
                         r'c:\Programs\monocle\monocle_v1.0.1')
        self.assertEqual(actual_monocle_tool.source_properties['target_path'], 
                         r'monocle')
        self.assertEqual(actual_monocle_tool.install_properties['source_path'], 
                         r'monocle')
        self.assertEqual(actual_monocle_tool.install_properties['target_path'], 
                         r'c:\monocle')
        
        #Tailor Tool Verification
        self.assertEqual(actual_tailor_tool.name, 'Tailor')
        self.assertEqual(actual_tailor_tool.os_type, 'Linux')
        self.assertEqual(actual_tailor_tool.os_arch, 'x64')
        self.assertEqual(actual_tailor_tool.version, '1.0')
        self.assertEqual(actual_tailor_tool.source_copy_once, True)
        self.assertEqual(actual_tailor_tool.source_type, 'basic_copy')
        self.assertEqual(actual_tailor_tool.install_type, 'basic_install')
        self.assertEqual(actual_tailor_tool.source_properties['source_path'], 
                         r'/mnt/builds/tailor/tailor_1.0')
        self.assertEqual(actual_tailor_tool.source_properties['target_path'], 
                         r'tailor')
        self.assertEqual(actual_tailor_tool.install_properties['source_path'], 
                         r'tailor')
        self.assertEqual(actual_tailor_tool.install_properties['target_path'], 
                         r'/opt/tailor')
        
        #Top Hat Tool Verification
        self.assertEqual(actual_top_hat_tool.name, 'Top Hat')
        self.assertEqual(actual_top_hat_tool.os_type, 'Windows')
        self.assertEqual(actual_top_hat_tool.os_arch, 'x64')
        self.assertEqual(actual_top_hat_tool.version, '12.0c')
        self.assertEqual(actual_top_hat_tool.source_copy_once, False)
        self.assertEqual(actual_top_hat_tool.source_type, 'ftp_copy')
        self.assertEqual(actual_top_hat_tool.install_type, 'basic_install')
        self.assertEqual(actual_top_hat_tool.source_properties['source_server'], 
                         r'ftp.fancylads.local')
        self.assertEqual(actual_top_hat_tool.source_properties['source_server_port'], 
                         r'21')
        self.assertEqual(actual_top_hat_tool.source_properties['source_server_user'], 
                         r'FancyCat')
        self.assertEqual(actual_top_hat_tool.source_properties['source_server_password'], 
                         r'meowmeowmeow')
        self.assertEqual(actual_top_hat_tool.source_properties['source_path'], 
                         r'Programs\tophat\tophat_12.0c')
        self.assertEqual(actual_top_hat_tool.source_properties['target_path'], 
                         r'tophat')
        self.assertEqual(actual_top_hat_tool.install_properties['source_path'], 
                         r'tophat')
        self.assertEqual(actual_top_hat_tool.install_properties['target_path'], 
                         r'c:\tophat')
        
        #Cobbler Tool Verification
        self.assertEqual(actual_cobbler_tool.name, 'Cobbler')
        self.assertEqual(actual_cobbler_tool.os_type, 'Windows')
        self.assertEqual(actual_cobbler_tool.os_arch, 'x86')
        self.assertEqual(actual_cobbler_tool.version, '1.0')
        self.assertEqual(actual_cobbler_tool.source_copy_once, False)
        self.assertEqual(actual_cobbler_tool.source_type, 'http_copy')
        self.assertEqual(actual_cobbler_tool.install_type, 'msi_install')
        self.assertEqual(actual_cobbler_tool.source_properties['source_server'], 
                         r'http.fancylads.local')
        self.assertEqual(actual_cobbler_tool.source_properties['source_server_port'], 
                         r'80')
        self.assertEqual(actual_cobbler_tool.source_properties['source_server_user'], 
                         r'FancyCat')
        self.assertEqual(actual_cobbler_tool.source_properties['source_server_password'], 
                         r'meowmeowmeow')
        self.assertEqual(actual_cobbler_tool.source_properties['source_path'], 
                         r'Programs\cobbler\cobbler_1.0')
        self.assertEqual(actual_cobbler_tool.source_properties['target_path'], 
                         r'cobbler')
        self.assertEqual(actual_cobbler_tool.install_properties['source_file'], 
                         r'Cobbler.msi')
        self.assertEqual(actual_cobbler_tool.install_properties['INSTALLLOCATION'], 
                         r'C:\cobbler')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!') 
    def test2_duplicate_tools(self):
        """Verify that you cannot have multiple tools with the same name in a ToolConfig."""
        
        with self.assertRaises(ConfigError) as cm:
            ToolConfig(SHARED_CONFIGS + r'tools/duplicate_tools.xml',
                       BESPOKE_XSD + r'/tool_config.xsd',
                       r'Tool')
             
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("Duplicate Tool name 'Monocle' specified, "
                                     "Tool names must be unique!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'tools/duplicate_tools.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')    
    def test3_tool_no_props(self):
        """Verify that Tools with no Properties are parsed correctly."""
        
        test_config = ToolConfig(SHARED_CONFIGS + r'tools/tools_no_props.xml',
                                 BESPOKE_XSD + r'/tool_config.xsd',
                                 r'Tool')
        
        actual_tool = test_config['NoProps']
                         
        self.assertEqual(actual_tool.name, 'NoProps')
        self.assertEqual(actual_tool.os_type, 'Windows')
        self.assertEqual(actual_tool.os_arch, 'x64')
        self.assertEqual(actual_tool.version, '13.1')
        self.assertEqual(actual_tool.source_copy_once, True)
        self.assertEqual(actual_tool.source_type, 'basic_copy')
        self.assertEqual(actual_tool.source_properties['source_path'], 
                         r'c:\Programs\monocle\monocle_v1.0.1')
        self.assertEqual(actual_tool.source_properties['target_path'],
                         r'monocle')
        self.assertEqual(actual_tool.install_type, 'no_install')
        self.assertEqual(len(actual_tool.install_properties), 0)
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test4_no_copy_type_bad_props(self):
        """Verify that the 'no_copy' source type does not accept any properties."""
        
        with self.assertRaises(ConfigError) as cm:
            ToolConfig(SHARED_CONFIGS + r'tools/bad_no_copy.xml',
                       BESPOKE_XSD + r'/tool_config.xsd',
                       r'Tool')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Tool 'BadNoCopy' has an error in the Source element: "
                                     "type 'no_copy' cannot have properties!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'tools/bad_no_copy.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test5_basic_copy_missing_props(self):
        """Verify that the 'basic_copy' source type checks for necessary properties."""
        
        with self.assertRaises(ConfigError) as cm:
            ToolConfig(SHARED_CONFIGS + r'tools/missing_basic_copy.xml',
                       BESPOKE_XSD + r'/tool_config.xsd',
                       r'Tool')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Tool 'MissingBasicCopy' has an error in the Source "
                                     "element: type 'basic_copy' is missing the 'target_path' "
                                     "property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'tools/missing_basic_copy.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')  
    def test6_ftp_copy_bad_props(self):
        """Verify that the 'ftp_copy' type does not accept any properties with invalid values."""
        
        with self.assertRaises(ConfigError) as cm:
            ToolConfig(SHARED_CONFIGS + r'tools/bad_ftp_copy.xml',
                       BESPOKE_XSD + r'/tool_config.xsd',
                       r'Tool')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Tool 'BadFTPCopy' has an error in the Source element: "
                                     "type 'ftp_copy' has a bad FQDN//IPv4 address for the "
                                     "'source_server' property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'tools/bad_ftp_copy.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test7_ftp_copy_missing_props(self):
        """Verify that the 'ftp_copy' type checks for necessary properties."""
        
        with self.assertRaises(ConfigError) as cm:
            ToolConfig(SHARED_CONFIGS + r'tools/missing_ftp_copy.xml',
                       BESPOKE_XSD + r'/tool_config.xsd',
                       r'Tool')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Tool 'MissingFTPCopy' has an error in the Source "
                                     "element: type 'ftp_copy' is missing the "
                                     "'source_server_password' property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'tools/missing_ftp_copy.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test8_http_copy_bad_props(self):
        """Verify that the 'http_copy' type does not accept any properties with invalid values."""
        
        with self.assertRaises(ConfigError) as cm:
            ToolConfig(SHARED_CONFIGS + r'tools/bad_http_copy.xml',
                       BESPOKE_XSD + r'/tool_config.xsd',
                       r'Tool')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Tool 'BadHTTPCopy' has an error in the Source element: "
                                     "type 'http_copy' has a bad FQDN//IPv4 address for the "
                                     "'source_server' property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'tools/bad_http_copy.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test9_http_copy_missing_props(self):
        """Verify that the 'http_copy' type checks for necessary properties."""
        
        with self.assertRaises(ConfigError) as cm:
            ToolConfig(SHARED_CONFIGS + r'tools/missing_http_copy.xml',
                       BESPOKE_XSD + r'/tool_config.xsd',
                       r'Tool')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Tool 'MissingHTTPCopy' has an error in the Source "
                                     "element: type 'http_copy' is missing the 'target_path' "
                                     "property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'tools/missing_http_copy.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!') 
    def test10_no_install_bad_props(self):
        """Verify that the 'no_install' install type does not accept any properties."""
        
        with self.assertRaises(ConfigError) as cm:
            ToolConfig(SHARED_CONFIGS + r'tools/bad_no_install.xml',
                       BESPOKE_XSD + r'/tool_config.xsd',
                       r'Tool')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Tool 'BadNoInstall' has an error in the InstallMethod "
                                     "element: type 'no_install' cannot have properties!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'tools/bad_no_install.xml')
       
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')  
    def test11_basic_install_bad_props(self):
        """Verify that the 'basic_install' type does not accept any properties with invalid values.
        """
        
        with self.assertRaises(ConfigError) as cm:
            ToolConfig(SHARED_CONFIGS + r'tools/bad_basic_install.xml',
                       BESPOKE_XSD + r'/tool_config.xsd',
                       r'Tool')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Tool 'BadBasicInstall' has an error in the InstallMethod "
                                     "element: type 'basic_install' has a bad path for the "
                                     "'source_path' property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'tools/bad_basic_install.xml')
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')    
    def test12_basic_install_missing_props(self):
        """Verify that the 'basic_install' install type checks for necessary properties."""
        
        with self.assertRaises(ConfigError) as cm:
            ToolConfig(SHARED_CONFIGS + r'tools/missing_basic_install.xml',
                       BESPOKE_XSD + r'/tool_config.xsd',
                       r'Tool')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Tool 'MissingBasicInstall' has an error in the "
                                     "InstallMethod element: type 'basic_install' is missing the "
                                     "'source_path' property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'tools/missing_basic_install.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test13_msi_install_bad_props(self):
        """ Verify that the 'msi_install' type does not accept any properties with invalid values.
        """
        
        with self.assertRaises(ConfigError) as cm:
            ToolConfig(SHARED_CONFIGS + r'tools/bad_msi_install.xml',
                       BESPOKE_XSD + r'/tool_config.xsd',
                       r'Tool')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Tool 'BadMSI' has an error in the InstallMethod element:"
                                     " type 'msi_install' has a bad path for the 'source_file' "
                                     "property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'tools/bad_msi_install.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test14_msi_install_missing_props(self):
        """Verify that the 'msi_install' install type checks for necessary properties."""
        
        with self.assertRaises(ConfigError) as cm:
            ToolConfig(SHARED_CONFIGS + r'tools/missing_msi_install.xml',
                       BESPOKE_XSD + r'/tool_config.xsd',
                       r'Tool')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Tool 'MissingMSI' has an error in the InstallMethod "
                                     "element: type 'msi_install' is missing the 'source_file' "
                                     "property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'tools/missing_msi_install.xml')
    
class BuildConfigTests(TestCase):
    """Tests for the BuildConfig class in the config module."""
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test1_happy_path(self):
        """Happy path test to verify that the BuildConfig class works."""
        
        test_config = BuildConfig(SHARED_CONFIGS + r'builds/happy_path.xml',
                                  BESPOKE_XSD + r'/build_config.xsd',
                                  r'Build')
        
        actual_monocle_tool = test_config['Monocle']
        actual_tailor_tool = test_config['Tailor']
        actual_top_hat_tool = test_config['Top Hat']
        actual_cobbler_tool = test_config['Cobbler']
        
        #Monocle Tool Verification
        self.assertEqual(actual_monocle_tool.name, 'Monocle')
        self.assertEqual(actual_monocle_tool.os_type, 'Windows')
        self.assertEqual(actual_monocle_tool.os_arch, 'x64')
        self.assertEqual(actual_monocle_tool.version, '1.0.1')
        self.assertEqual(actual_monocle_tool.source_copy_once, True)
        self.assertEqual(actual_monocle_tool.source_type, 'basic_copy')
        self.assertEqual(actual_monocle_tool.install_type, 'basic_install')
        self.assertEqual(actual_monocle_tool.source_properties['source_path'], 
                         r'c:\Programs\monocle\monocle_v1.0.1')
        self.assertEqual(actual_monocle_tool.source_properties['target_path'], 
                         r'monocle')
        self.assertEqual(actual_monocle_tool.install_properties['source_path'], 
                         r'monocle')
        self.assertEqual(actual_monocle_tool.install_properties['target_path'], 
                         r'c:\monocle')
        
        #Tailor Tool Verification
        self.assertEqual(actual_tailor_tool.name, 'Tailor')
        self.assertEqual(actual_tailor_tool.os_type, 'Linux')
        self.assertEqual(actual_tailor_tool.os_arch, 'x64')
        self.assertEqual(actual_tailor_tool.version, '1.0')
        self.assertEqual(actual_tailor_tool.source_copy_once, True)
        self.assertEqual(actual_tailor_tool.source_type, 'basic_copy')
        self.assertEqual(actual_tailor_tool.install_type, 'basic_install')
        self.assertEqual(actual_tailor_tool.source_properties['source_path'], 
                         r'/mnt/builds/tailor/tailor_1.0')
        self.assertEqual(actual_tailor_tool.source_properties['target_path'], 
                         r'tailor')
        self.assertEqual(actual_tailor_tool.install_properties['source_path'], 
                         r'tailor')
        self.assertEqual(actual_tailor_tool.install_properties['target_path'], 
                         r'/opt/tailor')
        
        #Top Hat Tool Verification
        self.assertEqual(actual_top_hat_tool.name, 'Top Hat')
        self.assertEqual(actual_top_hat_tool.os_type, 'Windows')
        self.assertEqual(actual_top_hat_tool.os_arch, 'x64')
        self.assertEqual(actual_top_hat_tool.version, '12.0c')
        self.assertEqual(actual_top_hat_tool.source_copy_once, False)
        self.assertEqual(actual_top_hat_tool.source_type, 'ftp_copy')
        self.assertEqual(actual_top_hat_tool.install_type, 'basic_install')
        self.assertEqual(actual_top_hat_tool.source_properties['source_server'], 
                         r'ftp.fancylads.local')
        self.assertEqual(actual_top_hat_tool.source_properties['source_server_port'], 
                         r'21')
        self.assertEqual(actual_top_hat_tool.source_properties['source_server_user'], 
                         r'FancyCat')
        self.assertEqual(actual_top_hat_tool.source_properties['source_server_password'], 
                         r'meowmeowmeow')
        self.assertEqual(actual_top_hat_tool.source_properties['source_path'], 
                         r'Programs\tophat\tophat_12.0c')
        self.assertEqual(actual_top_hat_tool.source_properties['target_path'], 
                         r'tophat')
        self.assertEqual(actual_top_hat_tool.install_properties['source_path'], 
                         r'tophat')
        self.assertEqual(actual_top_hat_tool.install_properties['target_path'], 
                         r'c:\tophat')
        
        #Cobbler Tool Verification
        self.assertEqual(actual_cobbler_tool.name, 'Cobbler')
        self.assertEqual(actual_cobbler_tool.os_type, 'Windows')
        self.assertEqual(actual_cobbler_tool.os_arch, 'x86')
        self.assertEqual(actual_cobbler_tool.version, '1.0')
        self.assertEqual(actual_cobbler_tool.source_copy_once, False)
        self.assertEqual(actual_cobbler_tool.source_type, 'http_copy')
        self.assertEqual(actual_cobbler_tool.install_type, 'msi_install')
        self.assertEqual(actual_cobbler_tool.source_properties['source_server'], 
                         r'http.fancylads.local')
        self.assertEqual(actual_cobbler_tool.source_properties['source_server_port'], 
                         r'80')
        self.assertEqual(actual_cobbler_tool.source_properties['source_server_user'], 
                         r'FancyCat')
        self.assertEqual(actual_cobbler_tool.source_properties['source_server_password'], 
                         r'meowmeowmeow')
        self.assertEqual(actual_cobbler_tool.source_properties['source_path'], 
                         r'Programs\cobbler\cobbler_1.0')
        self.assertEqual(actual_cobbler_tool.source_properties['target_path'], 
                         r'cobbler')
        self.assertEqual(actual_cobbler_tool.install_properties['source_file'], 
                         r'Cobbler.msi')
        self.assertEqual(actual_cobbler_tool.install_properties['INSTALLLOCATION'], 
                         r'C:\cobbler')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!') 
    def test2_duplicate_builds(self):
        """Verify that you cannot have multiple builds with the same name in a BuildConfig."""
        
        with self.assertRaises(ConfigError) as cm:
            BuildConfig(SHARED_CONFIGS + r'builds/duplicate_builds.xml',
                        BESPOKE_XSD + r'/build_config.xsd',
                        r'Build')
             
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("Duplicate Build name 'Monocle' specified, "
                                     "Build names must be unique!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'builds/duplicate_builds.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')    
    def test3_build_no_props(self):
        """Verify that Tools with no Properties are parsed correctly."""
        
        test_config = BuildConfig(SHARED_CONFIGS + r'builds/builds_no_props.xml',
                                  BESPOKE_XSD + r'/build_config.xsd',
                                  r'Build')
        
        actual_tool = test_config['NoProps']
                         
        self.assertEqual(actual_tool.name, 'NoProps')
        self.assertEqual(actual_tool.os_type, 'Windows')
        self.assertEqual(actual_tool.os_arch, 'x64')
        self.assertEqual(actual_tool.version, '13.1')
        self.assertEqual(actual_tool.source_copy_once, True)
        self.assertEqual(actual_tool.source_type, 'basic_copy')
        self.assertEqual(actual_tool.source_properties['source_path'], 
                         r'c:\Programs\monocle\monocle_v1.0.1')
        self.assertEqual(actual_tool.source_properties['target_path'],
                         r'monocle')
        self.assertEqual(actual_tool.install_type, 'no_install')
        self.assertEqual(len(actual_tool.install_properties), 0)
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test4_no_copy_type_bad_props(self):
        """Verify that the 'no_copy' source type does not accept any properties."""
        
        with self.assertRaises(ConfigError) as cm:
            BuildConfig(SHARED_CONFIGS + r'builds/bad_no_copy.xml',
                        BESPOKE_XSD + r'/build_config.xsd',
                        r'Build')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Build 'BadNoCopy' has an error in the Source element: "
                                     "type 'no_copy' cannot have properties!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'builds/bad_no_copy.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test5_basic_copy_missing_props(self):
        """Verify that the 'basic_copy' source type checks for necessary properties."""
        
        with self.assertRaises(ConfigError) as cm:
            BuildConfig(SHARED_CONFIGS + r'builds/missing_basic_copy.xml',
                        BESPOKE_XSD + r'/build_config.xsd',
                        r'Build')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Build 'MissingBasicCopy' has an error in the Source "
                                     "element: type 'basic_copy' is missing the 'target_path' "
                                     "property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'builds/missing_basic_copy.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')  
    def test6_ftp_copy_bad_props(self):
        """Verify that the 'ftp_copy' type does not accept any properties with invalid values."""
        
        with self.assertRaises(ConfigError) as cm:
            BuildConfig(SHARED_CONFIGS + r'builds/bad_ftp_copy.xml',
                        BESPOKE_XSD + r'/build_config.xsd',
                        r'Build')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Build 'BadFTPCopy' has an error in the Source element: "
                                     "type 'ftp_copy' has a bad FQDN//IPv4 address for the "
                                     "'source_server' property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'builds/bad_ftp_copy.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test7_ftp_copy_missing_props(self):
        """Verify that the 'ftp_copy' type checks for necessary properties."""
        
        with self.assertRaises(ConfigError) as cm:
            BuildConfig(SHARED_CONFIGS + r'builds/missing_ftp_copy.xml',
                        BESPOKE_XSD + r'/build_config.xsd',
                        'Build')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Build 'MissingFTPCopy' has an error in the Source "
                                     "element: type 'ftp_copy' is missing the "
                                     "'source_server_password' property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'builds/missing_ftp_copy.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test8_http_copy_bad_props(self):
        """Verify that the 'http_copy' type does not accept any properties with invalid values."""
        
        with self.assertRaises(ConfigError) as cm:
            BuildConfig(SHARED_CONFIGS + r'builds/bad_http_copy.xml',
                        BESPOKE_XSD + r'/build_config.xsd',
                        r'Build')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Build 'BadHTTPCopy' has an error in the Source element: "
                                     "type 'http_copy' has a bad FQDN//IPv4 address for the "
                                     "'source_server' property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'builds/bad_http_copy.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test9_http_copy_missing_props(self):
        """Verify that the 'http_copy' type checks for necessary properties."""
        
        with self.assertRaises(ConfigError) as cm:
            BuildConfig(SHARED_CONFIGS + r'builds/missing_http_copy.xml',
                        BESPOKE_XSD + r'/build_config.xsd',
                        r'Build')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Build 'MissingHTTPCopy' has an error in the Source "
                                     "element: type 'http_copy' is missing the 'target_path' "
                                     "property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'builds/missing_http_copy.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!') 
    def test10_no_install_bad_props(self):
        """Verify that the 'no_install' install type does not accept any properties."""
        
        with self.assertRaises(ConfigError) as cm:
            BuildConfig(SHARED_CONFIGS + r'builds/bad_no_install.xml',
                        BESPOKE_XSD + r'/build_config.xsd',
                        r'Build')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Build 'BadNoInstall' has an error in the InstallMethod "
                                     "element: type 'no_install' cannot have properties!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'builds/bad_no_install.xml')
       
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')  
    def test11_basic_install_bad_props(self):
        """Verify that the 'basic_install' type does not accept any properties with invalid values.
        """
        
        with self.assertRaises(ConfigError) as cm:
            BuildConfig(SHARED_CONFIGS + r'builds/bad_basic_install.xml',
                        BESPOKE_XSD + r'/build_config.xsd',
                        r'Build')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Build 'BadBasicInstall' has an error in the InstallMethod "
                                     "element: type 'basic_install' has a bad path for the "
                                     "'source_path' property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'builds/bad_basic_install.xml')
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')    
    def test12_basic_install_missing_props(self):
        """Verify that the 'basic_install' install type checks for necessary properties."""
        
        with self.assertRaises(ConfigError) as cm:
            BuildConfig(SHARED_CONFIGS + r'builds/missing_basic_install.xml',
                        BESPOKE_XSD + r'/build_config.xsd',
                        r'Build')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Build 'MissingBasicInstall' has an error in the "
                                     "InstallMethod element: type 'basic_install' is missing the "
                                     "'source_path' property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'builds/missing_basic_install.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test13_msi_install_bad_props(self):
        """ Verify that the 'msi_install' type does not accept any properties with invalid values.
        """
        
        with self.assertRaises(ConfigError) as cm:
            BuildConfig(SHARED_CONFIGS + r'builds/bad_msi_install.xml',
                        BESPOKE_XSD + r'/build_config.xsd',
                        r'Build')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Build 'BadMSI' has an error in the InstallMethod element:"
                                     " type 'msi_install' has a bad path for the 'source_file' "
                                     "property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'builds/bad_msi_install.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test14_msi_install_missing_props(self):
        """Verify that the 'msi_install' install type checks for necessary properties."""
        
        with self.assertRaises(ConfigError) as cm:
            BuildConfig(SHARED_CONFIGS + r'builds/missing_msi_install.xml',
                        BESPOKE_XSD + r'/build_config.xsd',
                        r'Build')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("The Build 'MissingMSI' has an error in the InstallMethod "
                                     "element: type 'msi_install' is missing the 'source_file' "
                                     "property!"))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'builds/missing_msi_install.xml')

class TestRunConfigTests(TestCase):
    """Tests for the TestRunConfig class in the config module."""
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test1_happy_path(self):
        """Happy path test to verify that the TestRunConfig class works."""
        
        actual = TestRunConfig(SHARED_CONFIGS + r'test_run/happy_path.xml',
                               BESPOKE_XSD + r'/test_run_config.xsd')
        
        #Basic information verification
        self.assertEqual(actual['Description'], 'Death Ray Tests')
        self.assertEqual(actual['EmailSender'], 'bespoke@fancylads.com')
        self.assertEqual(actual['EmailSubject'], 'Death Ray Test Results')
        self.assertSequenceEqual(actual['EmailRecipients'], 
                                 ['rgard@fancylads.com','cmoniot@fancylads.com'])
        self.assertEqual(actual['SMTPServer'], 'bespoke.fancylads.local')
        self.assertEqual(actual['port'], 587)
        self.assertEqual(actual['Username'], 'Fred')
        self.assertEqual(actual['Password'], 'punchbowl')
        self.assertEqual(actual['security_type'], 'TLS')
        self.assertEqual(actual['self_signed'], False)
        self.assertSequenceEqual(actual['ToolConfigs'], ['ToolConfig_1.xml'])
        self.assertSequenceEqual(actual['BuildConfigs'], ['BuildConfig_1.xml'])
        self.assertSequenceEqual(actual['TestPlans'], ['DeathRay_TestPlan.xml'])
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test2_bad_email_sender(self):
        """Verify that bad sender email addresses are caught."""
        
        with self.assertRaises(ConfigError) as cm:
            TestRunConfig(SHARED_CONFIGS + r'test_run/bad_email_sender.xml',
                          BESPOKE_XSD + r'/test_run_config.xsd')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ('The element "EmailSender" with the text '
                                     '"be@spoke@fancy#@lads.com" has invalid text format!'))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'test_run/bad_email_sender.xml')
    
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test3_bad_email_recipient(self):
        """Verify that bad recipient email addresses are caught."""
        
        with self.assertRaises(ConfigError) as cm:
            TestRunConfig(SHARED_CONFIGS + r'test_run/bad_email_recipient.xml',
                          BESPOKE_XSD + r'/test_run_config.xsd')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ('The element "EmailRecipient" with the text '
                                     '"rg##$@ard@fancylads.com" has invalid text format!'))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'test_run/bad_email_recipient.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test4_bad_email_server(self):
        """Verify that an invalid email server address is caught."""
        
        with self.assertRaises(ConfigError) as cm:
            TestRunConfig(SHARED_CONFIGS + r'test_run/bad_email_server.xml',
                          BESPOKE_XSD + r'/test_run_config.xsd')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ('The element "SMTPServer" with the text '
                                     '"bespoke.fancy_____lads..local" has invalid text format!'))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'test_run/bad_email_server.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test5_bad_port(self):
        """Verify that an invalid SMTP port is caught."""
        
        with self.assertRaises(ConfigError) as cm:
            TestRunConfig(SHARED_CONFIGS + r'test_run/bad_port.xml',
                          BESPOKE_XSD + r'/test_run_config.xsd')
        
        #Make sure exception contains correct ConfigError information.
        excep = cm.exception
        self.assertEqual(excep.msg, ('The element "SMTPServer" with the attribute "port" has '
                                     'invalid text format for attribute!'))
        self.assertEqual(excep._config_file, SHARED_CONFIGS + r'test_run/bad_port.xml')
        
    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test5_numeric_self_signed(self):
        """Verify that a numeric boolean value is accepted and converted correctly for
        the "self_signed" attribute.
        """
        
        actual = TestRunConfig(SHARED_CONFIGS + r'test_run/numeric_self_signed.xml',
                               BESPOKE_XSD + r'/test_run_config.xsd')
        
        self.assertEqual(actual['self_signed'], True)