"""
.. module:: hypervisor_mock_test
   :platform: Linux, Windows
   :synopsis: Unit tests for hypervisor module that are fully stubbed and mocked. This allows the
       the tests to be ran in any environment.
   :license: BSD, see LICENSE for more details.

.. moduleauthor:: Ryan Gard <ryan.a.gard@outlook.com>
"""
__version__ = 0.1

#===================================================================================================
# Imports
#===================================================================================================
from unittest import TestCase, skip
from mock import patch
#===================================================================================================
# Classes
#===================================================================================================
class _VboxStub(object):
    """This stub class provides dummy methods, attributes and properties for
    the 'IVirtualBox' interface class in the 'vboxapi' module.
    
    Args:
        None.
        
    Raises:
        None.
    """
    
    def __init__(self):
        self._machine = _MachineStub()
        
    def findMachine(self, nameOrId):
        """Attempts to find a virtual machine given its name or UUID.
        
        Args:
            nameOrId (str): What to search for. This can either be the UUID or the name of a 
                virtual machine.
        
        Returns:
            (_MachineStub)
        
        Raises:
            None.
        """
        
        return self._machine

class _WebSessionMgrStub(object):
    """This stub class provides dummy methods, attributes and properties for
    the 'IWebsessionManager' interface class in the 'vboxapi' module.
    
    Args:
        None.
        
    Raises:
        None.
    """
    
    def __init__(self):
        self._session = _SessionStub()
        
    def getSessionObject(self, refIVirtualBox):
        """Returns a managed object reference to the internal ISession object that was created for
        this web service session when the client logged on.  
        
        Args:
            refIVirtualBox (_VboxStub): The VirtualBox instance to use for session object.
        
        Returns:
            (_SessionStub)
        
        Raises:
            None.
        """
        
        return self._session
    
class _VboxManagerStub(object):
    """This stub class provides dummy methods, attributes and properties for
    the 'vboxapi.VirtualBoxManager' class.
    
    Args:
        None.
        
    Raises:
        None.
    """
    
    def __init__(self):
        self.vbox = _VboxStub()
        self.mgr = _WebSessionMgrStub()
    
    def closeMachineSession(self, session):
        """Close a session on a machine.
        
        Args:
            session (_SessionStub): The session to close.
        
        Returns:
            None.
        
        Raises:
            None.
        """
        
        pass
    
class _MachineStub(object):
    """This stub class provides dummy methods, attributes and properties for
    the 'vboxapi.VirtualBoxManager' class.
    
    Args:
        None.
        
    Raises:
        None.
    """
    
    def __init__(self):
        self.state = ''
        self._progress = _ProgressStub()
        self._snapshot = _SnapshotStub()
        
    def launchVMProcess(self, session, vm_type, environment):
        """Close a session on a machine.
        
        Args:
            session (_SessionStub): Client session object to which the VM process will be connected 
                (this must be in "Unlocked" state).
            vm_type (str):     Front-end to use for the new VM process. The following are currently 
                supported:

                    "gui": VirtualBox Qt GUI front-end
                    "headless": VBoxHeadless (VRDE Server) front-end
                    "sdl": VirtualBox SDL front-end
                    "emergencystop": reserved value, used for aborting the currently running VM or 
                        session owner. In this case the session parameter may be null 
                        (if it is non-null it isn't used in any way), and the progress return value 
                        will be always null. The operation completes immediately.
            environment (str): Environment to pass to the VM process.
            
        Returns:
            (_ProgressStub)
        
        Raises:
            None.
        """
        
        return self._progress
    
    def lockMachine(self, session, lockType):
        """Close a session on a machine.
        
        Args:
            session (_SessionStub): Session object for which the machine will be locked.
            lockType (int): If set to Write, then attempt to acquire an exclusive write lock or 
                fail. If set to Shared, then either acquire an exclusive write lock or establish a 
                link to an existing session.
        
        Returns:
            None.
        
        Raises:
            None.
        """
        
        pass
    
    def findSnapshot(self, nameOrId):
        """Returns a snapshot of this machine with the given name or UUID.
        
        Args:
            nameOrId (_SessionStub): Client session object to which the VM process will be connected 
                (this must be in "Unlocked" state).
        
        Returns:
            (_SnapshotStub)
        
        Raises:
            None.
        """
        
        return self._snapshot
    
class _SessionStub(object):
    """This stub class provides dummy methods, attributes and properties for
    the 'ISession' interface class in the 'vboxapi' module.
    
    Args:
        None.
        
    Raises:
        None.
    """
    
    def __init__(self):
        self.state = ''
        self.console = _ConsoleStub()
        
    def unlockMachine(self):
        """Unlocks a machine that was previously locked for the current session.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            None.
        """
        
        pass
    
class _ProgressStub(object):
    """This stub class provides dummy methods, attributes and properties for
    the 'IProgress' interface class in the 'vboxapi' module.
    
    Args:
        None.
        
    Raises:
        None.
    """
    
    def waitForCompletion(self, timeout):
        """Waits until the task is done (including all sub-operations) with a given timeout in
        milliseconds; specify -1 for an indefinite wait. 
        
        Args:
            timeout (int): Maximum time in milliseconds to wait or -1 to wait indefinitely.
        
        Returns:
            None.
        
        Raises:
            None.
        """
        
        pass

class _ConsoleStub(object):
    """This stub class provides dummy methods, attributes and properties for
    the 'IConsole' interface class in the 'vboxapi' module.
    
    Args:
        None.
        
    Raises:
        None.
    """
    
    def __init__(self):
        self.state = ''
        self._progress = _ProgressStub()
        
    def powerDown(self):
        """Initiates the power down procedure to stop the virtual machine execution.
        
        Args:
            None.
        
        Returns:
            (_ProgressStub)
        
        Raises:
            None.
        """
        
        return self._progress

    def reset(self):
        """Resets the virtual machine.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            None.
        """
        
        pass
    
    def restoreSnapshot(self, snapshot):
        """Starts resetting the machine's current state to the state contained in the given
        snapshot, asynchronously. 
        
        Args:
            snapshot (_SnapshotStub): The snapshot to restore the VM state from.
        
        Returns:
            (_ProgressStub)
        
        Raises:
            None.
        """
        
        return self._progress
    
class _SnapshotStub(object):
    """This stub class provides dummy methods, attributes and properties for
    the 'ISnapshot' interface class in the 'vboxapi' module.
    
    Args:
        None.
        
    Raises:
        None.
    """
    
    pass

#===================================================================================================
# Tests
#===================================================================================================
class VBoxMachineTests(TestCase):
    """Happy path tests for the VBoxMachine class in the hypervisor module."""
    
    def setUp(self):
        patcher = patch('vboxapi.VirtualBoxManager')
        self.addCleanup(patcher.stop)
        self.virtual_box_manager_mock = patcher.start()
        self.virtual_box_manager_mock.return_value = _VboxManagerStub()
        
        from hypervisor import VBoxMachine
        self.test_vm = VBoxMachine('localhost', 'fake')
        
    def test1_start_vm(self):
        """Verify that a stopped VM can be started."""
        
        #Set the machine state to "Stopped"
        self.test_vm._machine.state = 1
        
        #Set the session lock state to "Locked"
        self.test_vm._mgr.mgr._session.state = 2
        
        self.test_vm.start()
    
    def test2_restart_vm(self):
        """Verify that a running VM can be restarted."""
        
        #Set the machine state to "Running"
        self.test_vm._machine.state = 5
        
        #Set the session lock state to "Locked"
        self.test_vm._mgr.mgr._session.state = 2
        
        self.test_vm.restart()
        
    def test3_stop_vm(self):
        """Verify that a running VM can be stopped."""
        
        #Set the machine state to "Running"
        self.test_vm._machine.state = 5
        
        #Set the session lock state to "Locked"
        self.test_vm._mgr.mgr._session.state = 2
        
        self.test_vm.stop()
    
    def test4_apply_snapshot(self):
        """Verify that a snapshot can be applied to a powered off machine."""
        
        #Set the machine state to "Stopped"
        self.test_vm._machine.state = 1
        
        #Set the session lock state to "Locked"
        self.test_vm._mgr.mgr._session.state = 2
        
        self.test_vm.apply_snapshot('Basic')
        
class VBoxMachineTests_Negative(TestCase):
    """Negative tests for the VBoxMachine class in the hypervisor module."""
    
    def setUp(self):
        patcher = patch('vboxapi.VirtualBoxManager')
        self.addCleanup(patcher.stop)
        self.virtual_box_manager_mock = patcher.start()
        self.virtual_box_manager_mock.return_value = _VboxManagerStub()
        
        from hypervisor import VBoxMachine
        self.test_vm = VBoxMachine('localhost', 'fake')
        
    def test1_start_running_vm(self):
        """Attempt to start an  already running VM."""
        from hypervisor import VMError  #Import local to avoid screwing up mock.
        
        #Set the machine state to "Running"
        self.test_vm._machine.state = 5
        
        #Set the session lock state to "Locked"
        self.test_vm._mgr.mgr._session.state = 2
        
        with self.assertRaises(VMError) as cm:
            self.test_vm.start()
             
        #Make sure exception contains correct error information.
        excep = cm.exception
        self.assertEqual(excep.msg, "Virtual machine must be in stopped state before starting!")
        self.assertEqual(excep.host, 'localhost')
        self.assertEqual(excep.vm_name, 'fake')
    
    def test2_restart_stopped_vm(self):
        """Attempt to restart a stopped VM."""
        from hypervisor import VMError  #Import local to avoid screwing up mock.
        
        #Set the machine state to "Stopped"
        self.test_vm._machine.state = 1
        
        #Set the session lock state to "Locked"
        self.test_vm._mgr.mgr._session.state = 2
        
        with self.assertRaises(VMError) as cm:
            self.test_vm.restart()
             
        #Make sure exception contains correct error information.
        excep = cm.exception
        self.assertEqual(excep.msg, "Virtual machine must be in a running state before restarting!")
        self.assertEqual(excep.host, 'localhost')
        self.assertEqual(excep.vm_name, 'fake')
    
    def test3_stop_vm(self):
        """Attempt to stop a stopped VM."""
        from hypervisor import VMError  #Import local to avoid screwing up mock.
        
        #Set the machine state to "Stopped"
        self.test_vm._machine.state = 1
        
        #Set the session lock state to "Locked"
        self.test_vm._mgr.mgr._session.state = 2
        
        with self.assertRaises(VMError) as cm:
            self.test_vm.stop()
             
        #Make sure exception contains correct error information.
        excep = cm.exception
        self.assertEqual(excep.msg, "Virtual machine must be in a running state before stopping!")
        self.assertEqual(excep.host, 'localhost')
        self.assertEqual(excep.vm_name, 'fake')
        
    def test4_apply_snapshot_to_running_vm(self):
        """Attempt to apply a snapshot to a running vm."""
        from hypervisor import VMError  #Import local to avoid screwing up mock.
        
        #Set the machine state to "Running"
        self.test_vm._machine.state = 5
        
        #Set the session lock state to "Locked"
        self.test_vm._mgr.mgr._session.state = 2
        
        with self.assertRaises(VMError) as cm:
            self.test_vm.apply_snapshot('Basic')
             
        #Make sure exception contains correct error information.
        excep = cm.exception
        self.assertEqual(excep.msg, ("Virtual machine must be in stopped state before applying "
                                     "snapshot!"))
        self.assertEqual(excep.host, 'localhost')
        self.assertEqual(excep.vm_name, 'fake')
        