"""
.. module:: runtime
   :platform: Linux, Windows
   :synopsis: This module contains classes related to performing runtime operations for Bespoke.
   :license: BSD, see LICENSE for more details.

.. moduleauthor:: Ryan Gard <ryan.a.gard@outlook.com>
"""
__version__ = 0.1

# ===================================================================================================
# Imports
# ===================================================================================================
from os.path import join
from util import merge_dictionaries
from core import TestRun, BespokeGlobals
from config import BuildConfig, ToolConfig, GlobalConfig, ResourceConfig, TestRunConfig, \
ConfigError, TestPlanConfig

# ===================================================================================================
# Globals
# ===================================================================================================
GLOBAL_CONFIG_XSD = 'global_config.xsd'
TEST_RUN_CONFIG_XSD = 'test_run_config.xsd'
RESOURCE_CONFIG_XSD = 'resource_config.xsd'
BUILD_CONFIG_XSD = 'build_config.xsd'
TOOL_CONFIG_XSD = 'tool_config.xsd'
TEST_PLAN_XSD = 'test_plan.xsd'

# ===================================================================================================
# Exceptions
# ===================================================================================================
class ExecutionError(Exception):
    """Exception for errors in the runtime module.
    
    Args:
        msg (str): A message describing the error.
    """
    
    def __init__(self, msg):
        self.message = self.msg = msg
        
    def __str__(self):
        return "Execution Error: {0}".format(self.msg)
    
# ===================================================================================================
# Classes
# ===================================================================================================
class ExecuteTestRun(object):
    """This class will parse, validate configurations files necessary for a Bespoke test run. This
    class is the main access point to executing a test run with Bespoke.
    
    Args:
        bespoke_root |str| = The base path from which Bespoke executes on the server.
        xsd_path |str| = The absolute path to the XSD folder.  
        global_config_file |str| = The absolute path to the global configuration file.
        test_run_file |str| = The absolute path to the test run configuration file.
        resource_config_files <opt>|[str]| = An optional override to use for the resource 
            configuration files (paths must be absolute).
        test_plan_files <opt>|[str]| = An optional override to use for the test plan file paths
             (paths must be absolute).
        tools_config_files <opt>|[str]| = An optional override to use for the tool configuration 
            file paths (paths must be absolute).
        build_config_files <opt>|[str]| = An optional override to use for the build configuration 
            file paths (paths must be absolute).
        
    Raises:
        :class:`ExecutionError` = Could not load configuration files for a variety of reasons.
    """
    
    def __init__(self, 
                 bespoke_root,
                 xsd_path,
                 global_config_file, 
                 test_run_file,
                 resource_config_files=[],
                 test_plan_files=[], 
                 tools_config_files=[],
                 build_config_files=[]):
        
        ## init ##
        self._bespoke_root = bespoke_root
        self._xsd_path = xsd_path
        self._global_config_file = global_config_file #Path must be absolute.
        self._test_run_file = test_run_file
        self._resource_config_files = resource_config_files
        self._test_plan_files = test_plan_files
        self._tools_config_files = tools_config_files
        self._build_config_files = build_config_files
        
        ## XSD ##
        self._global_xsd_path = join(self._xsd_path, GLOBAL_CONFIG_XSD)
        self._test_run_xsd_path = join(self._xsd_path, TEST_RUN_CONFIG_XSD)
        self._resource_xsd_path = join(self._xsd_path, RESOURCE_CONFIG_XSD)
        self._build_xsd_path = join(self._xsd_path, BUILD_CONFIG_XSD)
        self._tool_xsd_path = join(self._xsd_path, TOOL_CONFIG_XSD)
        self._test_plan_xsd_path = join(self._xsd_path, TEST_PLAN_XSD)
        
        ## delayed init ##
        self._config_path = ''
        self._test_run_path = ''
        self._test_plan_path = ''
        self._test_script_path = ''
        self._resources = {}    #A merged dictionary of ResourceConfig content.
        self._global_config = None
        self._test_run_config = None
        self._builds = {}
        self._tools = {}
        self._test_plan_configs = []
        self._test_run = None
        
        ## load ##
        self._load_global()
        self._load_resources()
        self._load_test_run()
        self._load_builds()
        self._load_tools()
        self._load_test_plans()
        
        ## finalize test run ##
        self._build_test_run()
        
    def _build_test_run(self):
        """Pull all the test plans into a TestRun for eventual execution.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ExecutionError`
        """
        
        self._test_run = TestRun(self._test_run_config['Description'])
        
        for test_plan_config in self._test_plan_configs:
            self._test_run.add_test_plan(test_plan_config.get_content)
        
    def _load_builds(self):
        """Parse and load the build configuration files.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ExecutionError`
        """
        
        #A list of BuildConfig content dictionaries.
        tmp_builds = []
        
        try:
            for config in self._build_config_files:
                tmp_builds.append(BuildConfig(config, self._build_xsd_path, 'Build').get_content)
        except ConfigError as e:
            err = "Failure to load Build config file '{0}': {1}".format(e._config_file, e.msg)
            raise ExecutionError(err)
    
        if len(tmp_builds) == 0:
            self._builds = {}
        elif len(tmp_builds) > 1:
            try:
                self._builds = merge_dictionaries(tmp_builds, fail_on_duplicates=True)
            except KeyError as e:
                raise ExecutionError("Duplicate build names detected in build " 
                                     "configuration files: {}", e)
        else:
            self._builds = tmp_builds[0]
    
    def _load_global(self):
        """Parse and load the global configuration file.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ExecutionError`
        """
        
        try:
            self._global_config = GlobalConfig(self._global_config_file, self._global_xsd_path)
        except ConfigError as e:
            err = "Failure to load Global config file '{0}': {1}".format(e._config_file, e.msg)
            raise ExecutionError(err)
        
        #Determine paths for other configuration files.
        self._config_path = self._global_config['ConfigPath']
        self._test_run_path = self._global_config['TestRunPath']
        self._test_plan_path = self._global_config['TestPlanPath']
        self._test_script_path = self._global_config['TestScriptPath']
        
        #Parse and load the resource paths if no overrides are specified.
        if not self._resource_config_files:
            for config in self._global_config['ResourceConfigs']:
                self._resource_config_files.append(join(self._config_path, config))
                
        #Populate Bespoke Global Environment
        BespokeGlobals.ABS_LOCAL_RESULTS = self._global_config['ResultsPath']
        BespokeGlobals.ABS_LOCAL_TESTS = self._test_script_path
        BespokeGlobals.ABS_LOCAL_TOOLS = self._global_config['ToolPath']
        BespokeGlobals.BESPOKE_SERVER_HOSTNAME = self._global_config['BespokeServerHostname']
                
    def _load_resources(self):
        """Parse and load the resource configuration file.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ExecutionError`
        """
        
        #A list of ResourceConfig content dictionaries.
        tmp_resources = []
        
        try:
            for config in self._resource_config_files:
                tmp_resources.append(ResourceConfig(config, self._resource_xsd_path).get_content)
        except ConfigError as e:
            err = "Failure to load Resource config file '{0}': {1}".format(e._config_file, e.msg)
            raise ExecutionError(err)
    
        if len(tmp_resources) > 1:
            try:
                self._resources = merge_dictionaries(tmp_resources, fail_on_duplicates=True)
            except KeyError as e:
                raise ExecutionError("Duplicate aliases detected in resource " 
                                     "configuration files: {}", e)
        else:
            self._resources = tmp_resources[0]
            
    def _load_test_run(self):
        """Parse and load the test run configuration file.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ExecutionError`
        """
        
        try:
            self._test_run_config = TestRunConfig(join(self._test_run_path, self._test_run_file), 
                                                  self._test_run_xsd_path)
        except ConfigError as e:
            err = "Failure to load Test Run config file '{0}': {1}".format(e._config_file, e.msg)
            raise ExecutionError(err)
    
        #Parse and load the tool config paths if no overrides are specified.
        if len(self._tools_config_files) == 0:
            for config in self._test_run_config['ToolConfigs']:
                self._tools_config_files.append(join(self._config_path, config))
                
        #Parse and load the build config paths if no overrides are specified.
        if len(self._build_config_files) == 0:
            for config in self._test_run_config['BuildConfigs']:
                self._build_config_files.append(join(self._config_path, config))
                
        #Parse and load the test plan paths if no overrides are specified.
        if len(self._test_plan_files) == 0:
            for config in self._test_run_config['TestPlans']:
                self._test_plan_files.append(join(self._test_plan_path, config))
                
    def _load_test_plans(self):
        """Parse and load the test plan configuration files.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ExecutionError`
        """
        
        try:
            for config in self._test_plan_files:
                self._test_plan_configs.append(TestPlanConfig(config, 
                                                              self._test_plan_xsd_path,
                                                              self._builds,
                                                              self._tools,
                                                              self._resources))
        except ConfigError as e:
            err = "Failure to load Test Plan file '{0}': {1}".format(e._config_file, e.msg)
            raise ExecutionError(err)
    
    def _load_tools(self):
        """Parse and load the tool configuration files.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ExecutionError`
        """
        
        #A list of BuildConfig content dictionaries.
        tmp_tools = []
        
        try:
            for config in self._tools_config_files:
                tmp_tools.append(ToolConfig(config, self._tool_xsd_path, 'Tool').get_content)
        except ConfigError as e:
            err = "Failure to load Tool config file '{0}': {1}".format(e._config_file, e.msg)
            raise ExecutionError(err)
    
        if len(tmp_tools) == 0:
            self._tools = {}
        elif len(tmp_tools) > 1:
            try:
                self._tools = merge_dictionaries(tmp_tools, fail_on_duplicates=True)
            except KeyError as e:
                raise ExecutionError("Duplicate tool names detected in tool " 
                                     "configuration files: {}", e)
        else:
            self._tools = tmp_tools[0]
    
    def execute_test_run(self):
        """Execute the TestRun.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`FatalError`: Fatal error occurred and unreliable results possibly recorded.
            :class:`Failure`: The TestRun failed during execution.
        """
        
        self._test_run.execute()
        
    @property
    def builds(self):
        """A dictionary of Build objects.
        
        Returns:
            |{str::class:`Build`}|
        """
        
        return self._builds
    
    @property
    def global_config(self):
        """The GlobalConfig for this test run.
        
        Returns:
            |:class:`GlobalConfig`| = This looks like a dictionary.
        """
        
        return self._global_config
    
    @property
    def resources(self):
        """A dictionary of resources.
        
        Returns:
            |{str::class:`SystemUnderTest`}|
        """
        
        return self._test_run_config
    
    @property
    def test_run(self):
        """The TestRun object.
        
        Returns:
            |:class:`TestRun`|
        """
        
        return self._test_run
    
    @property
    def test_run_config(self):
        """The TestRunConfig for this test run.
        
        Returns:
            |:class:`TestRunConfig`| = This looks like a dictionary.
        """
        
        return self._test_run_config
    
    @property
    def tools(self):
        """A dictionary of Tool objects.
        
        Returns:
            |{str::class:`Tool`}|
        """
        
        return self._tools