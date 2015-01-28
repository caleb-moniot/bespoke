"""
.. module:: hypervisor
   :platform: Linux, Windows
   :synopsis: This module provides classes for managing Virtual Machines running
       on a Virtual Box host.
   :license: BSD, see LICENSE for more details.

.. moduleauthor:: Ryan Gard <ryan.a.gard@outlook.com>
"""
__version__ = 0.2

# ===================================================================================================
# Imports
# ===================================================================================================
import abc
from vboxapi import VirtualBoxManager
from util import retry

# ===================================================================================================
# Globals
# ===================================================================================================
VM_OP_TIMEOUT = 120 #Timeout for hypervisor VM related operations.
VBOX_WEB_PORT = '18083'

# ===================================================================================================
# Classes
# ===================================================================================================
class _VirtualMachine(object):
    """This abc defines the necessary functionality for virtual mahcines for any supported
    hypervisor.
    
    Args:
        host (str): The host of the machine that contains the target VM.
        name (str): The name of the virtual machine.
        
    Raises:
        :class:`VMError`: The Virtual Machine host was unreachable. The Virtual Machine name is 
            invalid.
    """
    
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, host, name):
        self._host = host
        self._name = name
    
    @abc.abstractproperty
    def current_state(self):
        """Report the current state of the VM.
        
        Args:
            None.
        
        Returns:
            (str): The current state of the VM.
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
            :class:`VMError`: The VM is no longer available or in a crappy state.
        """
        
        pass
    
    @property
    def host(self):
        """The host that contains this virtual machine.
        
        Args:
            None.
        
        Returns:
            (str)
        
        Raises:
            None.
        """
        
        return self._host
    
    @property
    def name(self):
        """The name of this virtual machine.
        
        Args:
            None.
        
        Returns:
            (str)
        
        Raises:
            None.
        """
        
        return self._name
    
    @abc.abstractmethod
    def setup(self):
        """Setup a virtual machine in preparation for use.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: An error occurred during virtual machine setup.
        """
        
        pass
    
    @abc.abstractmethod
    def tear_down(self):
        """Post use clean up tasks.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: An error occurred during virtual machine tear down.
        """
        
        pass
    
    @abc.abstractmethod
    def start(self):
        """Start the VM if stopped.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: State could not be changed or VM is not currently in the stopped 
                state.
        """
        
        pass
    
    @abc.abstractmethod
    def stop(self):
        """Stop the VM if started.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: State could not be changed or VM is not currently in the started 
                state.
        """
        
        pass
    
    @abc.abstractmethod
    def shutdown(self, wait):
        """Shutdown the VM via ACPI if the VM is running.
        
        Args:
            wait (bln) = Wait for shutdown to complete.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: State could not be changed or VM is not currently in the started 
                state.
        """
        
        pass
    
    @abc.abstractmethod
    def restart(self):
        """Restart the VM if started.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: State could not be changed or VM is not currently in the started 
                state.
        """
        
        pass
    
    @abc.abstractmethod
    def destroy(self):
        """Destroy the VM created from a template.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: VM could not be destroyed.
            :class:`NotSupported`: This function is not supported for this hypervisor.
        """
        
        pass
    
    @abc.abstractmethod
    def apply_snapshot(self, snapshot_name):
        """Apply a snapshot to the VM.
        
        Args:
            snapshot_name (str): Apply a snapshot to the VM.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: Snapshot failed to be applied or snapshot with given name not found.
            :class:`NotSupported`: This function is not supported for this hypervisor.
        """
        
        pass
    
class _VBoxHostManager(object):
    """Establishes connections to VirtualBox hosts and keeps a cached list of active VBoxManagers to
    minimize connection proliferation.
    
    Args:
        host (str): The host to use for the VirtualBox Manager connection.
        user (str)(opt): The user name to use for authentication if host is remote.
        password (str)(opt): The password to use for authentication if host is remote.
        
    Raises:
        :class:`VMError`: The Virtual Machine host was unreachable or invalid.
    """
    
    # ===============================================================================================
    # Class Variables
    # ===============================================================================================
    _vbox_managers = {}  #A dictionary of VBoxManager sessions keyed by host.
    
    def __init__(self, host, user=None, password=None):
        if host in _VBoxHostManager._vbox_managers:
            self._vboxmgr = _VBoxHostManager._vbox_managers[host]
        else:
            self._vbox_host_connect(host, user, password)
    
    def _vbox_host_connect(self, host, user=None, password=None):
        """Create a new connection to a VirtualBox host.
        
        Args:
            host (str): The host to use for the VirtualBox Manager connection.
            user (str)(opt): The user name to use for authentication if host is remote.
            password (str)(opt): The password to use for authentication if host is remote.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: The Virtual Machine host was unreachable or invalid.
        """
        
        self._vboxmgr = None
        
        try:
            if host == 'localhost' or host == '127.0.0.1':
                self._vboxmgr = VirtualBoxManager(None, None)
            else:
                if user is None or password is None:
                    raise Exception('You must supply a user and password for remote '
                                    'VirtualBox hosts!')

                self._vboxmgr = VirtualBoxManager('WEBSERVICE',
                                                  {'url':'http://{}:{}'.format(host, VBOX_WEB_PORT),
                                                   'user':user,
                                                   'password':password})
        except Exception:
            raise VMError('Cannot connect to VirtualBox host!', host=host)
        
        _VBoxHostManager._vbox_managers[host] = self._vboxmgr
    
    @property
    def manager(self):
        """The VirtualBoxManager host connection.
        
        Returns:
            (VirtualBoxManager)
        
        Raises:
            None.
        """
        
        return self._vboxmgr
    
class VBoxMachine(_VirtualMachine):
    """This class will allow access to static VirtualBox virtual machines on local and remote hosts.
    
    Args:
        host (str): The host of the machine that contains the target VM.
        name (str): The name of the virtual machine.
        user (str)(opt): The user name to use for authentication if host is remote.
        password (str)(opt): The password to use for authentication if host is remote.
        
    Raises:
        :class:`VMError`: The Virtual Machine host was unreachable. The Virtual Machine name is 
            invalid.
    """
    
    # ===============================================================================================
    # Class Constants
    # ===============================================================================================
    _MACHINE_STATES = {0: 'Bad', 
                       1: 'Stopped', 
                       2: 'Suspended', 
                       3: 'Bad', 
                       4: 'Bad', 
                       5: 'Running', 
                       6: 'Paused', 
                       7: 'Bad', 
                       8: 'Bad', 
                       9: 'Snapshotting', 
                       10: 'Starting', 
                       11: 'Stopping', 
                       12: 'Saving', 
                       13: 'Resuming', 
                       14: 'Bad', 
                       15: 'Bad', 
                       16: 'Bad', 
                       17: 'Snapshotting', 
                       18: 'Bad', 
                       19: 'Snapshotting', 
                       20: 'Snapshotting', 
                       21: 'Bad'}
    
    def __init__(self, host, name, user=None, password=None):
        super(VBoxMachine, self).__init__(host, name)
        
        self._mgr = _VBoxHostManager(host, user, password).manager
        self._vbox = self._mgr.vbox
        self._machine = None
        
        try:
            self._machine = self._vbox.findMachine(name)
        except Exception:
            raise VMError("No virtual machine by that name exists on the host!", 
                          self._host, 
                          self._name)
    @property
    def current_state(self):
        """Report the current state of the VM.
        
        Returns:
            (str): The current state of the VM.
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
            :class:`VMError`: The VM is no longer available or in a crappy state.
        """
        
        try:
            current_state = self._machine.state
        except Exception:
            raise VMError('Could not determine virtual machine state!', self._host, self._name)
        
        return self._MACHINE_STATES[current_state]
    
    @retry(5, exceptions=RuntimeError, delay=1)
    def _wait_for_state(self, state_object, expected_state):
        """Assert that an object has an attribute "state" at a given value.
        
        Args:
            state_object (obj): Any object with a "state" attribute.
            expected_state (obj): The desired state to wait for.
        
        Returns:
            None.
        
        Raises:
            RuntimeError: The state was not reached after 5 retries.
        """
        
        if state_object.state != expected_state:
            raise RuntimeError('The object does not have the desired state!')
    
    @retry(50, exceptions=RuntimeError, delay=1)
    def _wait_for_machine_state(self, expected_state):
        """Assert that the current machine state is at a given value.
        
        Args:
            expected_state (self._MACHINE_STATES): The desired machine state to wait for.
        
        Returns:
            None.
        
        Raises:
            VMError: The state was not reached after 50 retries.
        """
        
        if self.current_state != expected_state:
            raise RuntimeError('The machine state never reached the desired '
                               '"{0}" state!'.format(expected_state))
        
    def setup(self):
        """Setup a virtual machine in preparation for use.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: An error occurred during virtual machine setup.
        """
        
        #Nothing to do for static Virtual Box machines.
        pass
    
    def tear_down(self):
        """Post use clean up tasks.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: An error occurred during virtual machine tear down.
        """
        
        #Nothing to do for static Virtual Box machines.
        pass
    
    def start(self):
        """Start the VM if stopped.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: State could not be changed or VM is not currently in the stopped 
                state.
        """
        
        if self.current_state != 'Stopped':
            raise VMError('Virtual machine must be in stopped state before starting!', 
                          self._host,
                          self._name)
        
        try:
            session = self._mgr.mgr.getSessionObject(self._vbox)
            progress = self._machine.launchVMProcess(session, 'gui', '')
            progress.waitForCompletion(VM_OP_TIMEOUT)
            self._wait_for_state(session, 2)        #Wait for the "Locked" state. (2)
        except Exception as e:
            raise VMError('Failed to start the virtual machine! Reason: {}'.format(str(e)),
                          self._host,
                          self._name)
        finally:
            self._mgr.closeMachineSession(session)
        
    def stop(self):
        """Stop the VM if running.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: State could not be changed or VM is not currently in the started 
                state.
        """
        
        if self.current_state != 'Running':
            raise VMError('Virtual machine must be in a running state before stopping!', 
                          self._host,
                          self._name)
        
        try:
            session = self._mgr.mgr.getSessionObject(self._vbox)
            self._machine.lockMachine(session, 1)   #Shared lock.
            self._wait_for_state(session, 2)        #Wait for the "Locked" state. (2)
            progress = session.console.powerDown()  #Powerdown kills session and lock.
            progress.waitForCompletion(VM_OP_TIMEOUT)
            
            self._wait_for_machine_state('Stopped')
        except Exception as e:
            raise VMError('Failed to stop the virtual machine! Reason: {}'.format(str(e)),
                          self._host,
                          self._name)
    
    #TODO: Create unit test for this method.
    def shutdown(self, wait):
        """Shutdown the VM via ACPI if the VM is running.
        
        Args:
            wait (bln) = Wait for shutdown to complete.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: State could not be changed or VM is not currently in the started 
                state.
        """
        
        if self.current_state != 'Running':
            raise VMError('Virtual machine must be in a running state before stopping!', 
                          self._host,
                          self._name)
        
        try:
            session = self._mgr.mgr.getSessionObject(self._vbox)
            self._machine.lockMachine(session, 1)   #Shared lock.
            self._wait_for_state(session, 2)        #Wait for the "Locked" state. (2)
            session.console.powerButton()           #Send ACPI powerdown event.
            if not session.console.getPowerButtonHandled:
                raise RuntimeError("PowerButton event failed!")
            if wait:
                self._wait_for_machine_state('Stopped')
        except Exception as e:
            raise VMError('Failed to shutdown the virtual machine! Reason: {}'.format(str(e)),
                          self._host,
                          self._name)
        finally:
            self._mgr.closeMachineSession(session)
            
    #TODO: Split hard reset from soft restart.
    def restart(self):
        """Restart the VM if started.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: State could not be changed or VM is not currently in the started 
                state.
        """
        
        if self.current_state != 'Running':
            raise VMError('Virtual machine must be in a running state before restarting!', 
                          self._host,
                          self._name)
        
        try:
            session = self._mgr.mgr.getSessionObject(self._vbox)
            self._machine.lockMachine(session, 1)   #Shared lock.
            self._wait_for_state(session, 2)        #Wait for the "Locked" state. (2)
            session.console.reset()                 #Reset kills session and lock.
            session.unlockMachine()
        except Exception as e:
            raise VMError('Failed to restart the virtual machine! Reason: {}'.format(str(e)),
                          self._host,
                          self._name)

    def destroy(self):
        """Destroy the VM created from a template.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: VM could not be destroyed.
            :class:`NotSupported`: This function is not supported for this hypervisor.
        """
        
        raise NotSupported(host=self._host, vm_name=self._name)
    
    def _get_snapshot(self, snapshot_name):
        """Find and return a VBox snapshot interface object.
        
        Args:
            snapshot_name (str): The snapshot name to retrieve.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: No snapshot with the given name exists.
        """
        
        try:
            return self._machine.findSnapshot(snapshot_name)
        except Exception:
            raise VMError('Failed to find snapshot with the name "{}"!'.format(snapshot_name),
                          self._host,
                          self._name)

    def apply_snapshot(self, snapshot_name):
        """Apply a snapshot to the VM.
        
        Args:
            snapshot_name (str): Apply a snapshot to the VM.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: Machine is not in the stopped state, snapshot failed to be applied
                or snapshot with given name not found.
        """
        
        snapshot = self._get_snapshot(snapshot_name)
        
        if self.current_state != 'Stopped':
            raise VMError('Virtual machine must be in stopped state before applying snapshot!', 
                          self._host,
                          self._name)
        
        try:
            session = self._mgr.mgr.getSessionObject(self._vbox)
            self._machine.lockMachine(session, 1)       #Shared lock.
            self._wait_for_state(session, 2)            #Wait for the "Locked" state. (2)
            progress = session.console.restoreSnapshot(snapshot)
            progress.waitForCompletion(VM_OP_TIMEOUT)
            session.unlockMachine()
        except Exception as e:
            raise VMError('Failed to apply snapshot! Reason: {}'.format(str(e)),
                          self._host,
                          self._name)

class VagrantMachine(_VirtualMachine):
    """This class will allow access to VirtualBox virtual machines on local and remote hosts.
    
    Args:
        host (str): The host of the machine that contains the target VM.
        alias (str): The hostname (FQDN) used to contact the machine on a network.
        box_name (str): The Vagrant box name.
        box_url (str): The URL containing the Vagrant box file.
        provider (str): The hypervisor platform to run on.
        root (str): The vagrant working directory where vagrant configs are stored.
                
    Raises:
        :class:`VMError`: The Virtual Machine host was unreachable. The Virtual Machine name is 
            invalid.
    """
    
    # ===============================================================================================
    # Class Constants
    # ===============================================================================================
    _MACHINE_STATES = {0: 'Bad', 
                       1: 'Stopped', 
                       2: 'Suspended', 
                       3: 'Bad', 
                       4: 'Bad', 
                       5: 'Running', 
                       6: 'Paused', 
                       7: 'Bad', 
                       8: 'Bad', 
                       9: 'Snapshotting', 
                       10: 'Starting', 
                       11: 'Stopping', 
                       12: 'Saving', 
                       13: 'Resuming', 
                       14: 'Bad', 
                       15: 'Bad', 
                       16: 'Bad', 
                       17: 'Snapshotting', 
                       18: 'Bad', 
                       19: 'Snapshotting', 
                       20: 'Snapshotting', 
                       21: 'Bad'}
    
    def __init__(self, host, alias, box_name, box_url, provider, root, vagrant_file): #vmware_workstation, virtualbox, and vmware_fusion
        super(VagrantMachine, self).__init__(host, alias)
        self._box_name = box_name
        self._box_url = box_url
        self._provider = provider
        self._root = root
        self._vagrant_file = vagrant_file
                
    @property
    def current_state(self):
        """Report the current state of the VM.
        
        Returns:
            (str): The current state of the VM.
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
            :class:`VMError`: The VM is no longer available or in a crappy state.
        """
        
        try:
            current_state = self._machine.state
        except Exception:
            raise VMError('Could not determine virtual machine state!', self._host, self._name)
    
        return self._MACHINE_STATES[current_state]
    
    @retry(5, exceptions=RuntimeError, delay=1)
    def _wait_for_state(self, state_object, expected_state):
        """Assert that an object has an attribute "state" at a given value.
        
        Args:
            state_object (obj): Any object with a "state" attribute.
            expected_state (obj): The desired state to wait for.
        
        Returns:
            None.
        
        Raises:
            RuntimeError: The state was not reached after 5 retries.
        """
        
        if state_object.state != expected_state:
            raise RuntimeError('The object does not have the desired state!')
        
    def setup(self):
        """Setup a virtual machine in preparation for use.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: An error occurred during virtual machine setup.
        """
        
        #Call vagrant init. (Set hostname, or IP)
        pass
    
    def tear_down(self):
        """Post use clean up tasks.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: An error occurred during virtual machine tear down.
        """
        
        #Destory machine.
        pass
    
    def start(self):
        """Start the VM if stopped.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: State could not be changed or VM is not currently in the stopped 
                state.
        """
        
        if self.current_state != 'Stopped':
            raise VMError('Virtual machine must be in stopped state before starting!', 
                          self._host,
                          self._name)
        
        try:
            session = self._mgr.mgr.getSessionObject(self._vbox)
            progress = self._machine.launchVMProcess(session, 'gui', '')
            progress.waitForCompletion(VM_OP_TIMEOUT)
            self._wait_for_state(session, 2)        #Wait for the "Locked" state. (2)
            self._mgr.closeMachineSession(session)
        except Exception as e:
            raise VMError('Failed to start the virtual machine! Reason: {}'.format(str(e)),
                          self._host,
                          self._name)
        
    def stop(self):
        """Stop the VM if started.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: State could not be changed or VM is not currently in the started 
                state.
        """
        
        if self.current_state != 'Running':
            raise VMError('Virtual machine must be in a running state before stopping!', 
                          self._host,
                          self._name)
        
        try:
            session = self._mgr.mgr.getSessionObject(self._vbox)
            self._machine.lockMachine(session, 1)   #Shared lock.
            self._wait_for_state(session, 2)        #Wait for the "Locked" state. (2)
            progress = session.console.powerDown()  #Powerdown kills session and lock.
            progress.waitForCompletion(VM_OP_TIMEOUT)
        except Exception as e:
            raise VMError('Failed to stop the virtual machine! Reason: {}'.format(str(e)),
                          self._host,
                          self._name)
    
    def restart(self):
        """Restart the VM if started.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: State could not be changed or VM is not currently in the started 
                state.
        """
        
        if self.current_state != 'Running':
            raise VMError('Virtual machine must be in a running state before restarting!', 
                          self._host,
                          self._name)
        
        try:
            session = self._mgr.mgr.getSessionObject(self._vbox)
            self._machine.lockMachine(session, 1)   #Shared lock.
            self._wait_for_state(session, 2)        #Wait for the "Locked" state. (2)
            session.console.reset()                 #Reset kills session and lock.
            session.unlockMachine()
        except Exception as e:
            raise VMError('Failed to restart the virtual machine! Reason: {}'.format(str(e)),
                          self._host,
                          self._name)
    
    def _get_snapshot(self, snapshot_name):
        """Find and return a VBox snapshot interface object.
        
        Args:
            snapshot_name (str): The snapshot name to retrieve.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: No snapshot with the given name exists.
        """
        
        try:
            return self._machine.findSnapshot(snapshot_name)
        except Exception:
            raise VMError('Failed to find snapshot with the name "{}"!'.format(snapshot_name),
                          self._host,
                          self._name)
            
    def apply_snapshot(self, snapshot_name):
        """Apply a snapshot to the VM.
        
        Args:
            snapshot_name (str): Apply a snapshot to the VM.
        
        Returns:
            None.
        
        Raises:
            :class:`VMError`: Machine is not in the stopped state, snapshot failed to be applied
                or snapshot with given name not found.
        """
        
        snapshot = self._get_snapshot(snapshot_name)
        
        if self.current_state != 'Stopped':
            raise VMError('Virtual machine must be in stopped state before applying snapshot!', 
                          self._host,
                          self._name)
        
        try:
            session = self._mgr.mgr.getSessionObject(self._vbox)
            self._machine.lockMachine(session, 1)       #Shared lock.
            self._wait_for_state(session, 2)            #Wait for the "Locked" state. (2)
            progress = session.console.restoreSnapshot(snapshot)
            progress.waitForCompletion(VM_OP_TIMEOUT)
            session.unlockMachine()
        except Exception as e:
            raise VMError('Failed to apply snapshot! Reason: {}'.format(str(e)),
                          self._host,
                          self._name)
            
# ===================================================================================================
# Exceptions
# ===================================================================================================
class VMError(Exception):
    """Exception for errors in the hypervisor module.
    
    Args:
        msg (str): Human readable message of what the error is.
        host (str): The VM host machine.
        vm_name (str): The VM name.
        
    """
    
    def __init__(self, msg, host='', vm_name=''):
        self.message = self.msg = msg
        self.host = host
        self.vm_name = vm_name
        
    def __str__(self):
        return ("Hypervisor Error: {0} Host: {1} Virtual Machine: "
                "{2}".format(self.msg, self.host, self.vm_name))
        
class NotSupported(Exception):
    """Exception for unsupported functions in certain hypervisors.
    
    Args:
        msg (str): Human readable message of what the error is.
        host (str): The VM host machine.
        vm_name (str): The VM name.
        
    """
    
    def __init__(self, 
                 msg='This function is not supported for this hypervisor.', 
                 host='', 
                 vm_name=''):
        self.message = self.msg = msg
        self.host = host
        self.vm_name = vm_name
        
    def __str__(self):
        return ("Not Supported Error: {0} Host: {1} Virtual Machine: "
                "{2}".format(self.msg, self.host, self.vm_name))