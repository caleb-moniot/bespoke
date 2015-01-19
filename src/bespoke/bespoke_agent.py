#!/usr/bin/env python
"""
.. module:: wb_test_agent
   :platform: Linux, Windows
   :synopsis: The test agent will perform actions on behalf of Bespoke.
   :license: BSD, see LICENSE for more details.

.. moduleauthor:: Ryan Gard <ryan.a.gard@outlook.com>
"""
__version__ = 0.2

# ===================================================================================================
# Imports
# ===================================================================================================
import sys
import _winreg
import win32net
import win32netcon
from platform import platform, machine
from os import environ, makedirs
from os.path import join, isdir
from subprocess import check_call, CalledProcessError
from shutil import copytree
from PySTAF import STAFHandle, STAFException

# ===================================================================================================
# Functions
# ===================================================================================================
def staf_get_var(staf_handle, var_name):
    """Get a variable from a the local system var pool and return the object.
    The object is raw so the user will need to know what it is before using.
        
    Args:
        staf_handle (STAFHandle): An open STAF handle.
        var (str): The name of the variable.
    
    Returns:
        (obj): An object representing the variable.
    
    Raises:
        STAFException: The variable name does not exist or a general STAF
            error occurred when attempting to retrieve the variable.
    """

    staf_request = 'GET SYSTEM VAR {0}'.format(var_name)

    result = staf_handle.submit('local', 'var', staf_request)

    return result.resultObj


def xcopy(src, tgt):
    """Xcopy a tool from the Bespoke staging directory to a target location.
        
    Args:
        src (str) = The source directory.
        tgt (str) = The target directory.
    
    Returns:
        (bln)
    
    Raises:
        None.
    """

    try:
        copytree(src, tgt)
    except (WindowsError, IOError), e:
        print(e)
        return False

    return True


def msi(msi_path, msi_params):
    """Xcopy a tool from the Bespoke staging directory to a target location.
        
    Args:
        msi_path (str) = The path to the MSI.
        msi_params ({Param Name (str):Value (str)}): The parameters to pass to the MSI installer.
        
    Returns:
        (bln)
    
    Raises:
        None.
    """

    # Build the args for msiexec
    args = [join(environ['SYSTEMROOT'], 'system32', 'msiexec.exe')]

    args += ['/i', msi_path]

    # Build the custom params for the MSI.
    for x in msi_params:
        args.append('{0}={1}'.format(x, msi_params[x]))

    # Add the quiet and log switches. Always log the MSI transaction in the
    # user's temp folder.
    args += ['/quiet', '/log', join(environ['TMP'], 'msi.log')]

    try:
        check_call(args)
    except CalledProcessError:
        return False

    return True


def share_folder(share_name, path):
    """Share a folder on the machine with the most permissive access possible.
        
    Args:
        share_name (str): The name of the share.
        path (str): The path to the folder to share.
        
    Returns:
        (bln)
    
    Raises:
        None.
    """

    # First check to see if the target path exists, if not create it.
    if not isdir(path):
        try:
            makedirs(path)
        except (WindowsError, IOError), e:
            print(e)
            return False

    # We have to call into win32 to share the folder. First we need to build
    # a valid SHARE_INFO_2 struct.
    shinfo = {'netname': share_name,
              'type': win32netcon.STYPE_DISKTREE,
              'remark': 'Simple share.',
              'permissions': win32netcon.ACCESS_ALL,
              'max_uses': -1,
              'current_uses': 0,
              'path': path,
              'passwd': ''}

    try:
        win32net.NetShareAdd(None, 2, shinfo)
    except win32net.error, e:
        print(e)
        return False

    return True


def set_auto_logon(domain, username, password):
    """Change the auto logon for the VM to a different user.
        
    Args:
        domain (str) = The domain the user is part of.
        username (str) = The user.
        password (str) = The password.
        
    Returns:
        (bln)
    
    Raises:
        None.
    """

    # Registry info for the auto logon stuff.
    reg_path = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'
    reg_access = _winreg.KEY_WRITE

    # Determine the processor bitness.
    if machine() == 'AMD64':
        reg_access = reg_access | _winreg.KEY_WOW64_64KEY

    reg_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                              reg_path,
                              0,
                              reg_access)

    try:
        # Determine if the OS is Windows XP and set the domain if necessary.
        if platform(terse=True) == 'Windows-XP' or platform(terse=True) == 'Windows-2003Server':
            username = '{0}\\{1}'.format(domain, username)
        else:
            _winreg.SetValueEx(reg_key,
                               'DefaultDomainName',
                               0,
                               _winreg.REG_SZ,
                               domain)

        _winreg.SetValueEx(reg_key,
                           'DefaultUserName',
                           0,
                           _winreg.REG_SZ,
                           username)

        _winreg.SetValueEx(reg_key,
                           'DefaultPassword',
                           0,
                           _winreg.REG_SZ,
                           password)

        reg_key.Close()
    except WindowsError, e:
        print(e)
        return False

    return True


# ===================================================================================================
# Main
# ===================================================================================================
def main():
    staf_handle_name = 'wb_agent'  # The name of the handle.
    staf_handle = None  # The handle for communicating with STAF.

    wb_action = ''  # The action to perform.
    wb_params = {}  # The parameters to use for the action.

    exit_code = 1  # The exit code for the agent.

    try:
        staf_handle = STAFHandle(staf_handle_name, STAFHandle.Standard)
    except STAFException:
        sys.exit(1)

    # Grab the agent action and params.
    wb_action = staf_get_var(staf_handle, 'action')
    wb_params = staf_get_var(staf_handle, 'params')

    # Perform the requested action.
    if wb_action == 'Xcopy':
        exit_code = 0 if xcopy(wb_params['source_path'],
                               wb_params['target_path']) else 1
    elif wb_action == 'MSI':
        exit_code = 0 if msi(wb_params.pop('source_msi'), wb_params) else 1
    elif wb_action == 'ShareFolder':
        exit_code = 0 if share_folder(wb_params['share_name'],
                                      wb_params['path']) else 1
    elif wb_action == 'SetAutoLogon':
        exit_code = 0 if set_auto_logon(wb_params['Domain'],
                                        wb_params['User'],
                                        wb_params['Password']) else 1
    else:
        print("The action '{0}' is not recognized!".format(wb_action))

    # exit
    sys.exit(exit_code)


if __name__ == "__main__":
    main()