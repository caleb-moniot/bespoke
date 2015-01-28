"""
.. module:: core
   :platform: Linux, Windows
   :synopsis: This module contains classes that store test related information and
       provides test monitoring/reporting/functionality.
   :license: BSD, see LICENSE for more details.

.. moduleauthor:: Ryan Gard <ryan.a.gard@outlook.com>
"""
__version__ = 0.2

# ===================================================================================================
# Imports
# ===================================================================================================
import abc
from time import sleep
from collections import OrderedDict
from uuid import uuid1
from datetime import datetime, timedelta
from os.path import join, dirname, isdir, isfile
from PySTAF import STAFHandle, STAFException
from hypervisor import VMError
from util import retry, unix_style_path

# ===================================================================================================
# Globals
# ===================================================================================================
class BespokeGlobals(object):
    """This class contains global variables that are required to run Bespoke. Many of these
    variables need to be set at run time for Bespoke to work correctly.
    
    Args:
        None.
        
    Raises:
        None.
    """

    # The maximum amount of time a SystemUnderTest resource can be checked out in minutes.
    MAX_CHECKOUT_TIME = 7200

    # The amount of time to wait before SystemUnderTest checkout retry in seconds.
    VM_RETRY_WAIT = 30

    # Max number of retries for SystemUnderTest checkout in seconds.
    VM_RETRY_COUNT = 240

    # TODO: Make the VM_BOOT_WAIT configurable via the GlobalConfig XML.
    # The number of seconds to wait for SystemUnderTest boot in seconds.
    VM_BOOT_WAIT = 30

    # The number of retries for boot ping in seconds.
    PING_RETRY_COUNT = 5

    # The maximum amount of time for a TestCommand wait in seconds.
    MAX_TEST_COMMAND_WAIT = 500

    # TODO: This doesn't look to be necessary on the SUT.
    #The directory that stores configs on the SUT.
    CONFIGS = 'configs'

    # TODO: This doesn't look to be necessary on the SUT.
    # The directory that stores the test plans on the SUT.
    TEST_PLANS = 'testplans'

    # The directory that stores the builds on the SUT.
    BUILDS = 'builds'

    # The directory that stores the tools on the SUT.
    TOOLS = 'tools'

    # The directory that stores test scripts on the SUT.
    TESTS = 'tests'

    # The directory that stores test results on the SUT.
    RESULTS = 'results'

    # TODO: This doesn't look to be necessary on the SUT.
    # The directory that stores test reports on the SUT.
    REPORTS = 'reports'

    # Local Bespoke server hostname. Needs to be set at runtime.
    BESPOKE_SERVER_HOSTNAME = ''

    # TODO: Do we need to know this?
    # The local Bespoke root directory. Needs to be set at runtime.
    # BESPOKE_ROOT = ''

    # TODO: Do we need to know this?
    # The absolute local path to the configs. Needs to be set at runtime.
    # ABS_LOCAL_CONFIGS = ''

    # TODO: Do we need to know this?
    # The absolute local path to the test plans. Needs to be set at runtime.
    # ABS_LOCAL_TEST_PLANS = ''

    # TODO: Do we need to know this?
    # The absolute local path to the builds. Needs to be set at runtime.
    # ABS_LOCAL_BUILDS = ''

    # The absolute local path to the tools. Needs to be set at runtime.
    ABS_LOCAL_TOOLS = ''

    # The absolute local path to the test scripts. Needs to be set at runtime.
    ABS_LOCAL_TESTS = ''

    # The absolute local path to the results. Needs to be set at runtime.
    ABS_LOCAL_RESULTS = ''

    # TODO: Do we need to know this?
    # The absolute local path to the reports. Needs to be set at runtime.
    # ABS_LOCAL_REPORTS = ''

#===================================================================================================
# Exceptions
#===================================================================================================
class CoreError(Exception):
    """Exception for errors in the core module.
    
    Args:
        msg (str): A message describing the error.
    """

    def __init__(self, msg):
        self.message = self.msg = msg

    def __str__(self):
        return "Core Error: {0}".format(self.msg)

class FatalError(Exception):
    """Exception for fatal errors that require progress to be stopped on the current test plan.
    
    Args:
        msg (str): A message describing the error.
    """

    def __init__(self, msg):
        self.message = self.msg = msg

    def __str__(self):
        return "Fatal Error: {0}".format(self.msg)

class Failure(Exception):
    """Exception for _Test failures. (i.e. the action failed on the SystemUnderTest)
    
    Args:
        msg (str): A message describing the error.
    """

    def __init__(self, msg):
        self.message = self.msg = msg

    def __str__(self):
        return "Fatal Error: {0}".format(self.msg)

# ===================================================================================================
# Classes
# ===================================================================================================
class _Test(object):
    """This class is the abstract base class for all test classes. It provides the basic test
    execution and status.
    
    Args:
        name (str) = The name of the test.
        sut (:class:`SystemUnderTest`) = The SUT to execute remote STAF process calls against.
        
    Raises:
        None.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, name, sut):
        self._name = name
        self._sut = sut
        self._status = 'NotRan'
        self._staf_handle = None

    @abc.abstractmethod
    def execute(self):
        """Execute the test object and record results.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: An occurred that may be recoverable.
            :class:`FatalError`: A fatal error occurred and unreliable results may be recorded.
        """

        pass

    def _init_staf_handle(self):
        """Create a STAF handle.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`FatalError`: Failed to create a STAF handle.
        """

        try:
            self._staf_handle = STAFHandle(str(uuid1()), STAFHandle.Standard)
        except STAFException, e:
            raise FatalError("Error registering with STAF, RC: {0}, "
                             "Result: {1}".format(e.rc, e.result))

    def _close_staf_handle(self):
        """Close the STAF handle.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`FatalError`: Failed to unregister STAF handle.
        """

        try:
            self._staf_handle.unregister()
        except STAFException, e:
            raise FatalError("Error unregistering with STAF, RC: {0}, "
                             "Result: {1}".format(e.rc, e.result))

    def _create_remote_dir(self, directory):
        """Create a directory on the SUT.
        
        Args:
            directory = The directory to create on the SUT.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to create the directory on the SUT.
        """

        staf_request = ('CREATE DIRECTORY "{0}" FULLPATH '
                        'FAILIFEXISTS'.format(unix_style_path(directory)))

        result = self._staf_handle.submit(self._sut.network_address, 'fs', staf_request)

        if result.rc != result.Ok:
            raise CoreError(result.result)

    def _staf_dir_copy(self, local_path, remote_path):
        """Copy a directory from the local machine to the SUT.
        
        Args:
            local_path (str) = The local path from which to copy.
            remote_path (str) = The copy destination (absolute) on the SUT. 
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to copy the directory to the SUT.
        """

        staf_request = ('COPY DIRECTORY "{0}" TODIRECTORY "{1}" TOMACHINE "{2}" RECURSE '
                        'KEEPEMPTYDIRECTORIES'.format(unix_style_path(local_path),
                                                      unix_style_path(remote_path),
                                                      self._sut.network_address))

        result = self._staf_handle.submit('local', 'fs', staf_request)

        if result.rc != result.Ok:
            raise CoreError(result.result)

    def _staf_file_copy(self, local_path, remote_path, overwrite=True, is_text_file=False):
        """Copy a file from the local machine to the SUT.
        
        Args:
            local_path (str) = The local file path to copy.
            remote_path (str) = The copy destination (absolute) on the SUT.
            overwrite (bln)(opt) = Specify to enable overwrite or not.
            is_text_file (bln)(opt) = Specify if source file is text or not.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to copy the file to the SUT.
        """

        staf_create_request = ('CREATE DIRECTORY "{0}" '
                               'FULLPATH'.format(unix_style_path(dirname(remote_path))))

        result = self._staf_handle.submit(self._sut.network_address, 'fs', staf_create_request)

        if result.rc != result.Ok:
            raise CoreError(result.Ok)

        staf_copy_request = ('COPY FILE "{0}" TOFILE "{1}" '
                             'TOMACHINE "{2}"'.format(unix_style_path(local_path),
                                                      unix_style_path(remote_path),
                                                      self._sut.network_address))
        if is_text_file:
            staf_copy_request += ' TEXT'

        if not overwrite:
            staf_copy_request += ' FAILIFEXISTS'

        result = self._staf_handle.submit('local', 'fs', staf_copy_request)

        if result.rc != result.Ok:
            raise CoreError(result.result)

    def _staf_start_proc(self,
                         command,
                         working_dir,
                         wait,
                         params=[],
                         env_vars={},
                         location='local'):
        """Start a process via STAF.
        
        Args:
            command (str) = The command to execute.
            working_dir (str) = The working directory to start the process from within.
            wait (int) = The amount of time in seconds for STAF to wait before terminating the 
                process.
            params ([str])(opt) = A list of parameters to pass to the command.
            env_vars ({str:str:})(opt) = A dictionary of environment variables to set on the target 
                machine for the process.    
            location (str)(opt) = The machine to execute the process on.
        
        Returns:
            ((int), (str)) = The exit code of the "command" and the command output.
        
        Raises:
            :class:`CoreError`: The process failed to execute or the underlying command failed in 
                some way.
        """

        staf_request = ('START SHELL COMMAND "{0}" WORKDIR "{1}" WAIT '
                        '{2}s STDERRTOSTDOUT RETURNSTDOUT'.format(unix_style_path(command),
                                                                  unix_style_path(working_dir),
                                                                  str(wait)))
        if len(params) != 0:
            staf_request += ' PARMS {0}'.format(" ".join(params))

        if len(env_vars) != 0:
            for key in env_vars:
                staf_request += ' ENV {0}={1}'.format(key, env_vars[key])

        result = self._staf_handle.submit(location, 'process', staf_request)

        if result.rc != result.Ok:
            raise CoreError(result.result)

        #Return the exit code from the executed command and STDOUT.
        return (int(result.resultObj['rc']), result.resultObj['fileList'][0]['data'])

    @retry(BespokeGlobals.PING_RETRY_COUNT, CoreError, 1)
    def _ping(self):
        """This method will attempt to contact the target SystemUnderTest via STAF.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: The host was not available via STAF.
            :class:`FatalError`: Failure to communicate with the STAF service.
        """

        result = self._staf_handle.submit(self._sut.network_address, 'ping', 'ping')

        #16 is ping timeout for STAF
        if result.rc == result.NoPathToMachine:
            raise CoreError('Could not ping "{0}" '
                            'network address!'.format(self._sut.network_address))
        elif result.rc != result.Ok:
            raise FatalError(result.result)

    def _graceful_restart(self, wait):
        """Gracefully shutdown and then boot the SystemUnderTest.
        
        Args:
            wait (bln) = Wait for restart to complete.
        
        Returns:
            (bln)
        
        Raises:
            :class:`CoreError`: Restart failed, may be recoverable.
        """

        self._sut.shutdown(True)
        self._sut.start()

        if wait:
            sleep(BespokeGlobals.VM_BOOT_WAIT)

    @property
    def message(self):
        """A message attached to results. Most likely this is a message associated with a failure or
        fatal error.
        
        Returns:
            (str)
        """

        return self._message

    @property
    def name(self):
        """The name of the test.
        
        Returns:
            (str)
        """

        return self._name

    @property
    def status(self):
        """The current status of the test.
        
        Returns:
            (str):
                'NotRan'
                'Running'
                'Paused'
                'Pass'
                'Fail'
                'Fatal'
                'Critical'
        """

        return self._status

    @property
    def sut(self):
        """The SystemUnderTest associated with the test object.
        
        Returns:
            (:class:`SystemUnderTest`)
        """

        return self._sut

class _TestResults(_Test):
    """This class is the abstract base class for all test classes with result artifacts.
    
    Args:
        name (str) = The name of the test.
        sut (:class:`SystemUnderTest`) = The SUT to execute remote STAF process calls against.
        
    Raises:
        None.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, name, sut):
        super(_TestResults, self).__init__(name, sut)

        self._uuid = str(uuid1())
        self._local_results_path = join(BespokeGlobals.ABS_LOCAL_RESULTS, self._uuid)
        self._remote_results_path = join(self._sut.bespoke_root, BespokeGlobals.RESULTS, self._uuid)
        self._setup_has_ran = False

    def _setup_results(self):
        """Prepare the remote results directory.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to create the remote results directory.
            :class:`FatalError`: Failure to communicate with the STAF service.
        """

        self._ping()

        self._create_remote_dir(self._remote_results_path)

        self._setup_has_ran = True

    def _get_remote_results(self):
        """Copy the results from the SUT to the local machine.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to retrieve the remote results from SUT.
        """

        if not self._setup_has_ran:
            raise CoreError('The results object must be setup before executing!')

        staf_request = ('COPY DIRECTORY "{0}" TODIRECTORY "{1}" TOMACHINE "{2}" RECURSE '
                        'KEEPEMPTYDIRECTORIES'.format(unix_style_path(self._remote_results_path),
                                                      unix_style_path(self._local_results_path),
                                                      BespokeGlobals.BESPOKE_SERVER_HOSTNAME))

        result = self._staf_handle.submit(self._sut.network_address, 'fs', staf_request)

        if result.rc != 0:
            raise CoreError('Failed to copy the results directory '
                            '"{0}" from remote machine!'.format(self._remote_results_path))

    @abc.abstractmethod
    def execute(self):
        """Execute the test object and record results.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: An occurred that may be recoverable.
            :class:`FatalError`: A fatal error occurred and unreliable results may be recorded.
        """

        pass

    @property
    def local_results(self):
        """The local path containing the result artifacts from the test.
        
        Returns:
            (str)
        """

        return self._local_results_path

    @property
    def remote_results(self):
        """The path on the SUT that contains the result artifacts for the test.
        
        Returns:
            (str)
        """

        return self._remote_results_path

class _TestContainer(object):
    """This class is the abstract base class for container classes that hold _TestContainer or
    _Test objects.
    
    Args:
        name (str) = The name of the test container.
        
    Raises:
        None.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        self._name = name
        self._status = 'NotRan'
        self._message = ''

    @abc.abstractmethod
    def execute(self):
        """Execute the _Test or _TestContainer objects contained within this test container.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`Failure`: A _Test or _TestContainer object reported a failure..
            :class:`FatalError`: A fatal error occurred and unreliable results may be recorded.
        """

        pass

    @property
    def name(self):
        """The name of the test container.
        
        Returns:
            (str)
        """

        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def message(self):
        """The reason why a failure occurred.
        
        Returns:
            (str):
                'NotRan'
                'Running'
                'Paused'
                'Pass'
                'Fail'
                'Fatal'
        """

        return self._message

    @property
    def status(self):
        """The current status of the test.
        
        Returns:
            (str):
                'NotRan'
                'Running'
                'Paused'
                'Pass'
                'Fail'
                'Fatal'
        """

        return self._status

class _Installer(_TestResults):
    """This class is the abstract base class for all installers. It provides the basic tool
    staging support.
    
    Args:
        tool (:class:`Tool`) = The desired tool to use for installer.
        sut (:class:`SystemUnderTest`) = The SUT to execute remote STAF process calls against.
        timeout (int) = The number of seconds to wait before timing out installation.
        
    Raises:
        :class:`CoreError` = Fatal error occurred and unreliable results possibly recorded.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, tool, sut, timeout):
        super(_Installer, self).__init__("{0}_Installer".format(tool.name), sut)

        self._tool = tool
        self._timeout = timeout

    @abc.abstractmethod
    def _stage(self):
        """Stage the tool on the SUT for installation.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to stage the tool.
        """

        pass

    @abc.abstractmethod
    def _install(self):
        """Perform the installation of the tool on the SUT.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to install the tool.
        """

        pass

    @abc.abstractmethod
    def execute(self):
        """Install the tool onto the SUT.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`Fatal`: The _Installer failed during execution and no other testing can occur.
        """

        self._status = 'Running'

        try:
            self._init_staf_handle()
            self._setup_results()
            self._stage()
            self._install()
            self._get_remote_results()
            self._status = 'Pass'
        except CoreError as e:
            self._status = 'Fatal'
            self._message = e.msg
        finally:
            self._close_staf_handle()

        #Notify TestCase that a failure occurred.
        if self._status == 'Fatal': raise FatalError(self._message)

class BasicInstaller(_Installer):
    """Install a basic type tool onto a SUT.
    
    Args:
        tool (:class:`Tool`) = The desired tool to use for installer.
        sut (:class:`SystemUnderTest`) = The SUT to execute remote STAF process calls against.
        timeout (int) = The number of seconds to wait before timing out installation.
        
    Raises:
        :class:`CoreError` = Fatal error occurred and unreliable results possibly recorded.
    """

    def __init__(self, tool, sut, timeout):
        super(BasicInstaller, self).__init__(tool, sut, timeout)

    def _stage(self):
        """Stage the tool on the SUT for installation. (Note: this isn't necessary for basic
        install hence the empty function.)
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to stage the tool.
        """

        pass

    def _install(self):
        """Perform the installation of the tool on the SUT.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to install the tool.
        """

        local_source_path = join(BespokeGlobals.ABS_LOCAL_TOOLS,
                                 self._tool.install_properties['source_path'])

        remote_target_path = self._tool.install_properties['target_path']

        if isdir(local_source_path):
            self._staf_dir_copy(local_source_path, remote_target_path)
        elif isfile(local_source_path):
            self._staf_file_copy(local_source_path, remote_target_path)
        else:
            raise CoreError('Failed to stage tool "{0}" on remote machine! The file/directory '
                            '"{1}" does not exist!'.format(self._tool.name, local_source_path))

    def execute(self):
        """Install the tool onto the SUT.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Fatal error occurred and unreliable results possibly recorded.
        """

        super(BasicInstaller, self).execute()

class MSIInstaller(_Installer):
    """Install an MSI onto a Windows SUT.
    
    Args:
        tool (:class:`Tool`) = The desired tool to use for installer.
        sut (:class:`SystemUnderTest`) = The SUT to execute remote STAF process calls against.
        timeout (int) = The number of seconds to wait before timing out installation.
        
    Raises:
        :class:`CoreError` = Fatal error occurred and unreliable results possibly recorded.
    """

    def __init__(self, tool, sut, timeout):
        super(MSIInstaller, self).__init__(tool, sut, timeout)

        #For storing the remote path on the SUT.
        self._remote_target_path = None

    def _stage(self):
        """Stage the tool on the SUT for installation.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Fatal error occurred and unreliable results possibly recorded.
        """

        local_source_path = join(BespokeGlobals.ABS_LOCAL_TOOLS,
                                 self._tool.install_properties['source_file'])

        self._remote_target_path = join(self._sut.bespoke_root,
                                        BespokeGlobals.TOOLS,
                                        self._tool.install_properties['source_file'])

        if isfile(local_source_path):
            self._staf_file_copy(local_source_path, self._remote_target_path)
        else:
            raise CoreError('Failed to stage tool "{0}" on remote machine! The file/directory '
                            '"{1}" does not exist!'.format(self._tool.name, local_source_path))

    def _install(self):
        """Perform the installation of the tool on the SUT.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to stage the tool.
        """

        msi_command = 'msiexec'

        #Build a list of MSI params formatted correctly for MSI execution.
        msi_params = ['/i {0}'.format(self._remote_target_path),
                      '/qn',
                      '/L {0}//msi_install.log'.format(self._remote_results_path)]

        for key in self._tool.install_properties:
            if key != 'source_file':
                msi_params.append('{0}="{1}"'.format(key, self._tool.install_properties[key]))

        exit_code, out = self._staf_start_proc(msi_command,
                                               self._sut.bespoke_root,
                                               self._timeout,
                                               msi_params,
                                               location=self._sut.network_address)

        if exit_code != 0:
            raise CoreError('Failed to install tool "{0}": {1}'.format(self._tool.name, out))

    def execute(self):
        """Install the tool onto the SUT.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Fatal error occurred and unreliable results possibly recorded.
        """

        super(BasicInstaller, self).execute()

class Tool(object):
    """Store information about available tools.
    
    Args:
        name (str): The human readable name of the test.
        os_type (str): The target OS for the tool.
        os_arch (str): The taget CPU architecture for the tool. 
        version (str)(opt): The version number of the tool.
        source_type (str)(opt): The method to use to stage the tool.
        source_copy_once (bln)(opt): Only stage the tool if it hasn't be staged previously.
        install_type (str)(opt): The method to use to install the tool onto 
            the target SystemUnderTest.
        source_properties (dic)(opt): The properties needed by the source type.
            {Property Name (str):Property Value (str)} (Can be None)
        install_properties (dic)(opt): The properties needed by the install method type.
            {Property Name (str):Property Value (str)} (Can be None)
        build (bln)(opt): Indicates that the tool is a "build".
        
    Raises:
        None.
    """

    def __init__(self,
                 name,
                 os_type,
                 os_arch,
                 version='',
                 source_type='',
                 source_copy_once=False,
                 install_type='',
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
        """The name of the tool.
        
        Returns:
            (str)
        """

        return self._name

    @property
    def os_type(self):
        """The operating system type that the tool can be used with.
        
        Returns:
            (str)
        """

        return self._os_type

    @property
    def os_arch(self):
        """The operating system architecture (CPU) the tool is built for.
        
        Returns:
            (str)
        """

        return self._os_arch

    @property
    def version(self):
        """The version number of the tool.
        
        Returns:
            (str)
        """

        return self._version

    @property
    def source_type(self):
        """The method to use to stage the tool on the Bespoke server.
        
        Returns:
            (str)
        """

        return self._source_type

    @property
    def source_copy_once(self):
        """Only stage the tool if it hasn't be staged previously.
        
        Returns:
            (bln)
        """

        return self._source_copy_once

    @property
    def install_type(self):
        """The method to use to install the tool onto the target SystemUnderTest.
        
        Returns:
            (str)
        """

        return self._install_type

    @property
    def source_properties(self):
        """The properties needed by the source type.
        
        Returns:
            ({Property Name (str):Property Value (str)})
            (None)
        """

        return self._source_properties

    @property
    def install_properties(self):
        """The properties needed by the install method type.
        
        Returns:
            ({Property Name (str):Property Value (str)})
            (None)
        """

        return self._install_properties

    def stage(self):
        """Stage the tool on the Bespoke server.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Fatal error occurred and unreliable results possibly recorded.
        """
        pass

class Build(Tool):
    """Store information about available builds.
    
    Args:
        name (str): The human readable name of the test.
        os_type (str): The target OS for the build.
        os_arch (str): The taget CPU architecture for the build. 
        version (str)(opt): The version number of the build.
        source_type (str)(opt): The method to use to stage the build.
        source_copy_once (bln)(opt): Only stage the build if it hasn't be staged previously.
        install_type (str)(opt): The method to use to install the build onto 
            the target SystemUnderTest.
        source_properties (dic)(opt): The properties needed by the source type.
            {Property Name (str):Property Value (str)} (Can be None)
        install_properties (dic)(opt): The properties needed by the install method type.
            {Property Name (str):Property Value (str)} (Can be None)
        build (bln)(opt): Indicates that the build is a "build".
        
    Raises:
        None.
    """

    def __init__(self,
                 name,
                 os_type,
                 os_arch,
                 version='',
                 source_type='',
                 source_copy_once=False,
                 install_type='',
                 source_properties=None,
                 install_properties=None):

        super(Build, self).__init__(name,
                                    os_type,
                                    os_arch,
                                    version,
                                    source_type,
                                    source_copy_once,
                                    install_type,
                                    source_properties,
                                    install_properties)

class TestPrep(_Test):
    """This class will prepare the SystemUnderTest for testing. Also install necessary tools.
    
    Args:
        name (str) = The name of the test.
        sut (:class:`SystemUnderTest`) = The SUT to execute remote STAF process calls against.
        timeout (int) = The number of seconds to wait before timing out operations.
        postwait (int) = The number of seconds to wait post test before continuing.
        checkpoint (str)(opt) = The virtual machine checkpoint name to restore.
        
    Raises:
        None.
    """

    def __init__(self,
                 name,
                 sut,
                 timeout,
                 post_wait,
                 checkpoint=''):

        super(TestPrep, self).__init__(name, sut)

        self._checkpoint = checkpoint
        self._timeout = timeout
        self._post_wait = post_wait

    def _prep_vm(self):
        """Prepare the SystemUnderTest by applying snapshot if necessary.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: The SystemUnderTest is in a bad state or an operation failed.
        """

        if self._checkpoint != '':
            if self._sut.current_state() == 'Running':
                try:
                    self._sut.stop()
                except VMError as e:
                    raise CoreError("{} Host: {}, Virtual Machine: {}".format(e.msg,
                                                                              e.host,
                                                                              e.vm_name))
            try:
                self._sut.apply_snapshot(self._checkpoint)
                self._sut.start()
                sleep(BespokeGlobals.VM_BOOT_WAIT)
            except VMError as e:
                raise CoreError("{} Host: {}, Virtual Machine: {}".format(e.msg, e.host, e.vm_name))
        else:
            if self._sut.current_state() == 'Stopped':
                try:
                    self._sut.start()
                    sleep(BespokeGlobals.VM_BOOT_WAIT)
                except VMError as e:
                    raise CoreError("{} Host: {}, Virtual Machine: {}".format(e.msg,
                                                                              e.host,
                                                                              e.vm_nsame))
            if self._sut.current_state() not in ('Stopped', 'Running'):
                raise CoreError('The System Under Test "{}" is not '
                                'in a valid state for testing!'.format(self._sut.alias))

    def _install_bespoke(self):
        """Create the directory structure on target SystemUnderTest for Bespoke and install
        necessary modules along with the test agent.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to install Bespoke on the SUT.
        """

        #Delete any existing instances of Bespoke on remote machine.
        self._delete_root_dir()

        #Create the Bespoke directory structure.
        self._create_remote_dir(join(self._sut.bespoke_root, BespokeGlobals.BUILDS))
        self._create_remote_dir(join(self._sut.bespoke_root, BespokeGlobals.CONFIGS))
        self._create_remote_dir(join(self._sut.bespoke_root, BespokeGlobals.RESULTS))
        self._create_remote_dir(join(self._sut.bespoke_root, BespokeGlobals.TEST_PLANS))
        self._create_remote_dir(join(self._sut.bespoke_root, BespokeGlobals.TESTS))
        self._create_remote_dir(join(self._sut.bespoke_root, BespokeGlobals.TOOLS))

    def _delete_root_dir(self):
        """Delete the Bespoke root directory on the SUT if it exists.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to delete the Bespoke root directory on the SUT.
        """

        staf_request = ('DELETE ENTRY "{0}" RECURSE '
                        'CONFIRM '.format(unix_style_path(self._sut.bespoke_root)))

        result = self._staf_handle.submit(self._sut.network_address, 'fs', staf_request)

        if result.rc not in [result.Ok, result.DoesNotExist]:
            raise CoreError(result.result)

    def execute(self):
        """Prepare a target SystemUnderTest for testing.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`FatalError`: The TestPrep failed to install essential Bespoke components.
        """

        self._status = 'Running'

        try:
            self._init_staf_handle()
            self._prep_vm()
            self._ping()
            self._install_bespoke()
            sleep(self._post_wait)
            self._status = 'Pass'
        except CoreError as e:
            self._status = 'Fatal'
            self._message = e.msg
        finally:
            self._close_staf_handle()

        #Notify TestCase that a failure occurred.
        if self._status == 'Fatal': raise FatalError(self._message)

    @property
    def timeout(self):
        """The maximum amount of time to allow for execution.
        
        Returns:
            (int)
        """

        return self._timeout

class TestStep(_TestResults):
    """This class will copy tests to the SUT and execute them.
    
    Args:
        description (str) = The description of the test step.
        sut (:class:`SystemUnderTest`) = The SUT to execute remote STAF process calls against.
        test_directory (str) = The test directory holding the test executables and artifacts.
        interpreter (str) = The interpreter to use for executing the text executable.
        test_exec (str) = The test executable in the test directory to execute.
        test_params ({str:str}) = Parameters to pass to the test executable.
        timeout (int) = The number of seconds to wait before timing out operations.
        post_wait (int) = The number of seconds to wait post test before continuing.
        
    Raises:
        None.
    """

    def __init__(self,
                 description,
                 sut,
                 test_directory,
                 interpreter,
                 test_exec,
                 test_params,
                 timeout,
                 post_wait):

        super(TestStep, self).__init__(description, sut)

        self._description = self._name
        self._test_directory = test_directory
        self._interpreter = interpreter
        self._test_exec = test_exec
        self._test_params = test_params
        self._timeout = timeout
        self._post_wait = post_wait
        self._remote_target_path = join(self._sut.bespoke_root,
                                        BespokeGlobals.TESTS,
                                        self._test_directory)

    def _stage_test_step(self):
        """Copy test artifacts to SUT.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to copy test artifacts to SUT.
        """

        local_source_path = join(BespokeGlobals.ABS_LOCAL_TESTS, self._test_directory)

        if isdir(local_source_path):
            self._staf_dir_copy(local_source_path, self._remote_target_path)
        else:
            raise CoreError('Failed to stage test step "{0}" on remote machine! The test directory '
                            '"{1}" does not exist!'.format(self._description, local_source_path))

    def _execute_test_step(self):
        """Execute the test step executable on the SUT.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to execute test on SUT or test executable reported failure.
        """

        test_step_command = '{0}'.format(self._test_exec) if self._interpreter == '' else \
                            '{0} {1}'.format(self._interpreter, self._test_exec)

        # TODO: Expand user and environment variables.
        test_params = ['{0} {1}'.format(x,y) if y != '' else '{0}'.format(x)
                       for x,y in self._test_params.items()]

        exit_code, out = self._staf_start_proc(test_step_command,
                                               self._remote_target_path,
                                               self._timeout,
                                               test_params,
                                               location=self._sut.network_address)

        if exit_code != 0:
            raise CoreError('Test step "{0}" failed: {1}'.format(self._description, out))

    def execute(self):
        """Execute test steps on the SUT.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`Failure`: The TestStep failed during execution.
        """

        self._status = 'Running'

        try:
            self._init_staf_handle()
            self._setup_results()
            self._stage_test_step()
            self._execute_test_step()
            sleep(self._post_wait)
            self._get_remote_results()
            self._status = 'Pass'
        except CoreError as e:
            self._status = 'Fail'
            self._message = e.msg
        finally:
            self._close_staf_handle()

        #Notify TestCase that a failure occurred.
        if self._status == 'Fail': raise Failure(self._message)

    @property
    def timeout(self):
        """The maximum amount of time to allow for execution.
        
        Returns:
            (int)
        """

        return self._timeout

class TestCase(_TestContainer):
    """Install builds and execute a test on the target SystemUnderTest.
    
    Args:
        name (str) = The human readable name of the test case.
        
    Raises:
        None.
    """

    def __init__(self, name):
        super(TestCase, self).__init__(name)

        #A dictionary of TestPrep resources available via "resource_id".
        self._test_preps = {}    #{"resource_id":TestPrep}

        #The combined list of test preps, tools and steps to execute for the test case.
        self._tests = []

        #A list of SUT aliases that are currently associated with this test case.
        self._sut_aliases = []

    def _add_power_event(self, name, sut, event_type, wait):
        """Add a "PowerEvent" to the queue of "TestSteps".
        
        Args:
            name (str) = A human readable name for the power event.
            sut (:class:`SystemUnderTest`) = The SystemUnderTest to use for testing.
            event_type (str) = The type of power event to execute.
                (restart, shutdown)
            wait (bln) = A flag indicating whether or not to wait for the global wait time 
                currently VM_BOOT_WAIT.
                
        Returns:
            None.
        
        Raises:
            None.
        """

        self._tests.append(PowerControl("{0}_PowerControl".format(name), sut, event_type, wait))

    def _checkin_resources(self):
        """Check-in all resources for the test case.
        
        Args:
            None.
                
        Returns:
            None.
        
        Raises:
            None.
        """

        for test_prep in self._test_preps.values():
            test_prep.sut.checkin()

    def _checkout_resources(self):
        """Checkout resources for the test case. If resources aren't available then block until they
        are available.
        
        Args:
            None.
                
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: A resource is busy and cannot be checked-out.
            :class:`FatalError`: The resource timeout exceeds maximum.
        """

        for resource_id, test_prep in self._test_preps.iteritems():
            try:
                test_prep.sut.checkout(test_prep.timeout)
            except CoreError:
                self._checkin_resources()
                self._status = 'Fatal'
                self._message = ('The "{0}" resource is busy and cannot be checked-out by the '
                                 '"{1}" test case!'.format(resource_id, self.name))
                raise FatalError(self._message)
            except FatalError:
                self._checkin_resources()
                self._status = 'Fatal'
                self._message = ('The timeout "{0}" is not valid for resource "{1}" in the "{2}" '
                                 'test case!'.format(test_prep.timeout, resource_id, self.name))
                raise FatalError(self._message)

    def _update_resource_timeouts(self, timeout):
        """Update the timeout for all checked out resources.
        
        Args:
            timeout (int) = The number of seconds to lock the resource.
                
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: The resource has not been checked-out yet.
            :class:`FatalError`: The resource timeout exceeds maximum.
        """

        for resource_id, test_prep in self._test_preps.iteritems():
            try:
                test_prep.sut.update_lock_timeout(timeout)
            except CoreError:
                raise CoreError('The "{0}" resource is not currently checked out by the "{1}" '
                                'test case!'.format(resource_id, self.name))
            except FatalError:
                raise FatalError('The timeout "{0}" is not valid for resource "{1}" in the "{2}" '
                                 'test case!'.format(test_prep.timeout, resource_id, self.name))

    def add_build(self, sut, build, timeout):
        """Add a list of build for installation on SUT during test preparation.
        
        Args:
            sut (:class:`SystemUnderTest`) = The SystemUnderTest to use for testing.
            build (:class:`Build`) = The build to install on the SUT.
            timeout (int) = The number of seconds to wait before timing out installation.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Unsupported install_type.
        """

        if build.install_type == 'basic_install':
            self._tests.append(BasicInstaller(build, sut, timeout))
        elif build.install_type == 'msi_install':
            self._tests.append(MSIInstaller(build, sut, timeout))
        elif build.install_type == 'no_install':
            pass
        else:
            raise CoreError('The install_type "{0}" for build "{1}" '
                            'is unsupported!'.format(build.install_type, build.name))

    def add_resoure_refresh(self, resource_id, restart, restart_wait):
        """Add a "RefreshResource" to the list of "TestSteps".
        
        Args:
            resource_id (str) = The ID of the associated TestPrep to execute during testing.
            restart (bln) = Restart the computer after test step execution..
            restart_wait (bln) = Wait for restart to complete.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: The "ResourceRefresh" specified an invalid "resource_id".
        """

        if resource_id not in self._test_preps.keys():
            raise CoreError('The "{0}" resource_id specified for ResourceRefresh in TestCase "{1}" '
                            'is not valid!'.format(resource_id, self._name))

        sut = self._test_preps[resource_id].sut

        self._tests.append(self._test_preps[resource_id])

        if restart:
            self._add_power_event(resource_id, sut, 'restart', restart_wait)

    def add_test_prep(self,
                      resource_id,
                      sut,
                      checkpoint,
                      post_wait,
                      timeout,
                      restart,
                      restart_wait):

        """Add a "TestPrep" to the test case.
        
        Args:
            resource_id (str) = The ID to use for referring to the resource in subsequent
                test steps.
            sut (:class:`SystemUnderTest`) = The SystemUnderTest to use for testing.
            checkpoint (str) = The checkpoint to restore during test preparation.
            post_wait (int) = The number of seconds to wait post test preparation before continuing.
            timeout (int) = The number of seconds to wait before timing out during test preparation
                components.
            restart (bln) = Restart the computer after test step execution..
            restart_wait (bln) = Wait for restart to complete.
                
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: The requested "resource_id" is already in use by another "TestPep".
                The "TestPrep" requested the same SUT as another "TestPrep" already defined in 
                this test case.
        """

        if resource_id in self._test_preps.keys():
            raise CoreError('The "{0}" resource_id specified for TestPrep in TestCase "{1}" '
                            'already in use!'.format(resource_id, self._name))
        elif sut.alias in self._sut_aliases:
            raise CoreError('The alias "{0}" referenced by resource_id "{1}" for the TestPrep in '
                            'TestCase "{2}" is already in use!'.format(sut.alias,
                                                                       resource_id,
                                                                       self._name))

        try:
            tmp_test_prep = TestPrep(resource_id, sut, timeout, post_wait, checkpoint)
        except CoreError as e:
            raise CoreError('The TestCase "{0}" could not be created because of an error in the '
                            'TestPrep "{1}": {2}'.format(self._name, resource_id, e.msg))

        self._sut_aliases.append(sut.alias)
        self._test_preps[resource_id] = tmp_test_prep
        self._tests.append(self._test_preps[resource_id])

        if restart:
            self._add_power_event(resource_id, sut, 'restart', restart_wait)

    def add_test_step(self,
                      desc,
                      resource_id,
                      test_directory,
                      interpreter,
                      test_exec,
                      test_params,
                      timeout,
                      post_wait,
                      restart,
                      restart_wait):

        """Add a "TestStep" to the test case.
        
        Args:
            desc (str) = The description of the test step.
            resource_id (:class:`SystemUnderTest`) = The resource_id of the SystemUnderTest to use
                for test execution.
            test_directory (str) = The test directory holding the test executables and artifacts.
            interpreter (str) = The interpreter to use for executing the text executable.
            test_exec (str) = The test executable in the test directory to execute.
            test_params ({str:str}) = Parameters to pass to the test executable.
            timeout (int) = The number of seconds to wait before timing out operations.
            post_wait (int) = The number of seconds to wait post test before continuing.
            restart (bln) = Restart the computer after test step execution..
            restart_wait (bln) = Wait for restart to complete.
            
        Raises:
            None.
        
        Raises:
            :class:`CoreError`: The "TestStep" specified an invalid "resource_id". 
        """

        if resource_id not in self._test_preps.keys():
            raise CoreError('The "{0}" resource_id specified for TestStep "{1}" in TestCase "{2}" '
                            'is not valid!'.format(resource_id, desc, self._name))

        sut = self._test_preps[resource_id].sut

        self._tests.append(TestStep(desc,
                                    sut,
                                    test_directory,
                                    interpreter,
                                    test_exec,
                                    test_params,
                                    timeout,
                                    post_wait))

        if restart:
            self._add_power_event(desc, sut, 'restart', restart_wait)

    def add_tool(self, sut, tool, timeout):
        """Add a list of tool for installation on SUT during test preparation.
        
        Args:
            sut (:class:`SystemUnderTest`) = The SystemUnderTest to use for testing.
            tool (:class:`Tool`) = The tool to install on the SUT.
            timeout (int) = The number of seconds to wait before timing out installation.
            
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Unsupported install_type.
        """

        if tool.install_type == 'basic_install':
            self._tests.append(BasicInstaller(tool, sut, timeout))
        elif tool.install_type == 'msi_install':
            self._tests.append(MSIInstaller(tool, sut, timeout))
        elif tool.install_type == 'no_install':
            pass
        else:
            raise CoreError('The install_type "{0}" for tool "{1}" '
                            'is unsupported!'.format(tool.install_type, tool.name))

    def execute(self):
        """Execute the test case.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`FatalError`: Fatal error occurred and unreliable results possibly recorded.
            :class:`Failure`: The TestCase failed during execution.
        """

        self._status = 'Running'

        self._checkout_resources()

        for test in self._tests:
            try:
                self._update_resource_timeouts(test.timeout)
                test.execute()
            except Failure as e:
                self._status = 'Fail'
                self._message = ('The "{0}" test in the test case "{1}" failed with the '
                                 'message: "{2}"'.format(test.name, self.name, e.msg))
            except FatalError as e:
                self._checkin_resources()
                self._status = 'Fatal'
                self._message = ('The "{0}" test in the test case "{1}" encountered the fatal '
                                 'error: "{2}"'.format(test.name, self.name, e.msg))
                raise FatalError(self._message)

        if self._status == 'Fail':
            self._checkin_resources()
            raise Failure(self._message)

        self._status = 'Pass'
        self._checkin_resources()

class TestPlan(_TestContainer):
    """This is a simple container class for TestCases.
    
    Args:
        name (opt)(str) = The name of the test plan.
        
    Raises:
        None.
    """

    def __init__(self,  name=''):
        super(TestPlan, self).__init__(name)

        self._test_cases = OrderedDict()    #{test_case_name:TestCase}

    def add_test_case(self, test_case_name, test_case):
        """Add a test case to this test plan.
        
        Args:
            test_case_name (str) = The name of the test case.
            test_case (:class:`TestCase`) = A test case to add to the current test plan.
            
        Returns:
            None.
        
        Raises:
            None.
        """

        self._test_cases[test_case_name] = test_case

    def execute(self):
        """Execute the test plan.
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`FatalError`: Fatal error occurred and unreliable results possibly recorded.
            :class:`Failure`: The TestPlanConfig failed during execution.
        """

        self._status = 'Running'

        for test_case in self._test_cases.values():
            try:
                test_case.execute()
            except Failure as e:
                self._status = 'Fail'
                self._message = ('The "{0}" test case in the test plan "{1}" failed with the '
                                 'message: "{2}"'.format(test_case.name, self.name, e.msg))
            except FatalError as e:
                self._status = 'Fail'
                self._message = ('The "{0}" test case in the test plan "{1}" encountered the fatal '
                                 'error: "{2}"'.format(test_case.name, self.name, e.msg))
                raise FatalError(self._message)

        if self._status == 'Fail':
            raise Failure(self._message)

        self._status = 'Pass'

    @property
    def get_test_cases(self):
        """The test cases contained within the plan.
        
        Returns:
            ({str::class:`TestCase`:])
        """

        return self._test_cases

class TestRun(_TestContainer):
    """This is a simple container class for TestPlans.
    
    Args:
        name (str) = The name of the test run.
        
    Raises:
        None.
    """

    def __init__(self,  name):
        super(TestRun, self).__init__(name)

        self._test_plans = []

    def add_test_plan(self, test_plan):
        """Add a test plan to this test run.
        
        Args:
            test_plan (:class:`TestPlanConfig`) = A test plan to add to the current test run.
            
        Returns:
            None.
        
        Raises:
            None.
        """

        self._test_plans.append(test_plan)

    def execute(self):
        """Execute the test run..
        
        Args:
            None.
            
        Returns:
            None.
        
        Raises:
            :class:`FatalError`: Fatal error occurred and unreliable results possibly recorded.
            :class:`Failure`: The TestRun failed during execution.
        """

        self._status = 'Running'

        for test_plan in self._test_plans:
            try:
                test_plan.execute()
            except Failure as e:
                self._status = 'Fail'
                self._message = ('The "{0}" test plan in the test run "{1}" failed with the '
                                 'message: "{2}"'.format(test_plan.name, self.name, e.msg))
            except FatalError as e:
                self._status = 'Fail'
                self._message = ('The "{0}" test plan in the test run "{1}" encountered the fatal '
                                 'error: "{2}"'.format(test_plan.name, self.name, e.msg))
                raise FatalError(self._message)

        if self._status == 'Fail':
            raise Failure(self._message)

        self._status = 'Pass'

class SystemUnderTest(object):
    """A class that contains information about the system under test and functions for manipulating
    the state of the SUT.
    
    Args:
        alias (str): The alias for the SystemUnderTest.
        machine (_VirtualMachine): A _VirtualMachine object type used for controlling
            VM on the hypervisor host.
        bespoke_root (str): The installation path of bespoke on the SystemUnderTest.
        credentials ({Username(str):Password(str)}): Credentials to use to perform actions on the 
            SystemUnderTest.
        machine_type (str): The underlying machine type of the SystemUnderTest object.
            'static'
            'template'
        network_address (str): The network address at which to contact the SystemUnderTest.
        os (str): The operating system type of the SystemUnderTest.
        os_label (str): A human readable label of the operating system installed on the
            SystemUnderTest.
        arch_type (str): The processor architecture of the installed operating system. 
        role (str): The role that SystemUnderTest will be used as in a given testing scenario.
        check_points ({CheckPointName(str):Tools([str])}): The checkpoints and associated tools
            available on the SystemUnderTest.
        tools ([str]): A list of tools already installed on the SystemUnderTest for every
            checkpoint.
        
    Raises:
        :class:`CoreError`: An unknown machine type was specified.
    """

    #===============================================================================================
    # Class Constants
    #===============================================================================================
    _MACHINE_TYPES = ('static', 'template')

    def __init__(self,
                 alias,
                 machine,
                 bespoke_root,
                 credentials,
                 machine_type,
                 network_address,
                 os,
                 os_label,
                 arch_type,
                 role,
                 check_points,
                 tools):

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

        self._in_use = False
        self._lock_expiration = datetime.now()

        if self._machine_type not in self._MACHINE_TYPES:
            raise CoreError("The machine type '{0}' is not supported!".format(self._machine_type),False)

    @property
    def alias(self):
        """The alias for the SystemUnderTest.
        
        Returns:
            (str)
        """

        return self._alias

    @property
    def machine_type(self):
        """The underlying machine type of the SystemUnderTest object.
        
        Returns: (str)
            'static'
            'template'
        """

        return self._machine_type

    @property
    def bespoke_root(self):
        """The installation path of bespoke on the SystemUnderTest.
        
        Returns: (str)
        """

        return self._bespoke_root

    @property
    def credentials(self):
        """Credentials to use to perform actions on the SystemUnderTest.
        
        Returns: ({Username(str):Password(str)})
        """

        return self._credentials

    @property
    def network_address(self):
        """The address on the network at which the SystemUnderTest is reachable.
        
        Returns:
            (str)
        """

        return self._network_address

    @property
    def os(self):
        """The OS installed on the SystemUnderTest.
        
        Returns:
            (str)
        """

        return self._os

    @property
    def os_label(self):
        """A human readable label of the operating system installed on the SystemUnderTest.
        
        Returns:
            (str)
        """

        return self._os_label

    @property
    def arch_type(self):
        """The architecture of the processor of the SystemUnderTest.
        
        Returns:
            (str)
        """

        return self._arch_type

    @property
    def role(self):
        """A general description of the SystemUnderTest intended role.
        
        Returns:
            (str)
        """

        return self._role

    @property
    def check_points(self):
        """The checkpoints and associated tools available on the SystemUnderTest.
        
        Returns:
            ({CheckPointName(str):Tools([str])})
        """

        return self._check_points

    @property
    def tools(self):
        """All the tools available on the SytemUnderTest.
        
        Returns:
            (str)
        """

        return self._available_tools

    def checkout(self, timeout):
        """Reserve SystemUnderTest for a period of time.
        
        Args:
            timeout (int): The number of seconds to lock the resource.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: The resource is still busy.
            :class:`FatalError`: The provided timeout is not within range.
        """

        if not 0 < timeout <= BespokeGlobals.MAX_CHECKOUT_TIME:
            raise FatalError("Timeout is out of range!")
        elif self._in_use and (datetime.now() < self._lock_expiration):
            raise CoreError("This SystemUnderTest is in use currently!")
        elif self._in_use and (datetime.now() > self._lock_expiration):
            # A lock time out occurred and we need to force a checkin first.
            self.checkin()

        self._in_use = True
        self._lock_expiration = datetime.now() + timedelta(seconds=timeout)

        self._machine.setup()

    def update_lock_timeout(self, timeout):
        """Update the lock timeout for the SystemUnderTest for a period of time.
        
        Args:
            timeout (int): The number of seconds to lock the resource.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: The resource is not checked out currently.
            :class:`FatalError`: The provided timeout is not within range.
        """

        if not 0 < timeout <= BespokeGlobals.MAX_CHECKOUT_TIME:
            raise FatalError("Timeout is out of range!")
        elif not self._in_use:
            raise CoreError("This SystemUnderTest is not currently checked-out!")

        self._lock_expiration = datetime.now() + timedelta(seconds=timeout)

    def checkin(self):
        """Release the lock on the SystemUnderTest.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: The caller asking for the release is not the original owner of the
                lock.
        """

        if self._in_use:
            self._in_use = False
            self._lock_expiration = datetime.now()
            self._machine.tear_down()

    def current_state(self):
        """Report the current state of the SystemUnderTest.
        
        Args:
            None.
        
        Returns:
            (str): The current state of the SystemUnderTest.
                "Bad"
                "Running"
                "Stopped"
                "Paused"
                "Suspended"
                "Starting" 
                "Snapshotting"
                "Saving"
                "Stopping"
                "Pausing"
                "Resuming"
        
        Raises:
            :class:`CoreError`: The SystemUnderTest is no longer available or in a crappy state.
        """

        try:
            return self._machine.current_state
        except VMError, e:
            raise CoreError(e.msg, True)

    def start(self):
        """Start the SystemUnderTest.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to start SystemUnderTest.
        """

        try:
            self._machine.start()
        except VMError, e:
            raise CoreError(e.msg, True)

    def stop(self):
        """Stop the SystemUnderTest.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to stop SystemUnderTest.
        """

        try:
            self._machine.stop()
        except VMError, e:
            raise CoreError(e.msg, True)

    def restart(self):
        """Restart the SystemUnderTest.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to restart SystemUnderTest.
        """

        try:
            self._machine.restart()
        except VMError, e:
            raise CoreError(e.msg, True)

    def shutdown(self, wait):
        """Shutdown the SystemUnderTest using ACPI if available.
        
        Args:
            wait (bln) = Wait for shutdown to complete.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to shutdown SystemUnderTest.
        """

        try:
            self._machine.shutdown(wait)
        except VMError, e:
            raise CoreError(e.msg, True)

    def apply_snapshot(self, name):
        """Apply a snapshot to the SystemUnderTest.
        
        Args:
            name (str): The name of the snapshot to apply.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: The snapshot name does not exist or the snapshot failed to be 
                applied.
        """

        try:
            self._machine.apply_snapshot(name)
        except VMError, e:
            raise CoreError(e.msg, True)

class PowerControl(_Test):
    """Send the power events 'shutdown' and 'restart' to the SUT.
    
    Args:
        name (str) = The human readable name of the power control event.
        sut (:class:`SystemUnderTest`) = The SUT to execute remote power control event on.
        power_event_type (str) = The type of power control event to initalize on the SUT 
            (restart, shutdown).
        wait (bln) = A flag indicating whether or not to wait for the global wait time 
            (currently VM_BOOT_WAIT).
        
    Raises:
        None.
    """

    def __init__(self, name, sut, power_event_type, wait):
        super(PowerControl, self).__init__(name, sut)

        self._power_event_type = power_event_type
        self._wait = wait
        self._command_timeout = 10

    def _linux_power_control(self):
        """Issue power control commands to a Linux platform SUT.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to execute the power command.
        """

        os_power_command = 'shutdown -r now' if self._power_event_type == 'restart' \
            else 'shutdown -h now'

        exit_code, out = self._staf_start_proc(os_power_command,
                                               self._sut.bespoke_root,
                                               self._command_timeout,
                                               location = self._sut.network_address)

        if exit_code != 0:
            raise CoreError('Power control event "{0}" failed: {1}'.format(self._name, out))

    def _windows_power_control(self):
        """Issue power control commands to a Windows platform SUT.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`CoreError`: Failed to execute the power command.
        """

        os_power_command = 'shutdown /r /t 3' if self._power_event_type == 'restart' \
            else 'shutdown /h /t 3'

        exit_code, out = self._staf_start_proc(os_power_command,
                                               self._sut.bespoke_root,
                                               self._command_timeout,
                                               location = self._sut.network_address)

        if exit_code != 0:
            raise CoreError('Power control event "{0}" failed: {1}'.format(self._name, out))

    def execute(self):
        """Execute power control event on the target SUT.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`FatalError`: The power control event failed.
        """

        self._status = 'Running'

        try:
            self._init_staf_handle()
            self._ping()

            if self._sut.os == 'Linux':
                self._linux_power_control()
            elif self._sut.os == 'Windows':
                self._windows_power_control()
            else:
                raise CoreError("Unknown OS platform: {0}".format(self._sut.os))

            if self._wait:
                sleep(BespokeGlobals.VM_BOOT_WAIT)

            self._status = 'Pass'
        except CoreError as e:
            self._status = 'Fatal'
            self._message = e.msg
        finally:
            self._close_staf_handle()

        #Notify TestCase that a failure occurred.
        if self._status == 'Fatal': raise FatalError(self._message)
        
