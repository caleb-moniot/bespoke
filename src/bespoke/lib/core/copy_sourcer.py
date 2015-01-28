"""
.. module:: core.file_sourcer
   :platform: Linux, Windows
   :synopsis: This module contains classes that provide file/directory
   copying from multiple types of sources to a local directory.
   :license: BSD, see LICENSE for more details.

.. moduleauthor:: Caleb Moniot <cmoniot@gmail.com>
"""
__version__ = 0.1

# ===================================================================================================
# Imports
# ===================================================================================================
import abc
import shutil
import win32wnet
import errno
from os import makedirs
from ftplib import FTP
from os.path import isdir, isfile, basename, dirname, exists

# ===================================================================================================
# Globals
# ===================================================================================================

# ===================================================================================================
# Classes 
# ===================================================================================================
class _CopySourcer(object):
    """This class provides functions for copying files from a remote source to a local destination.
    
    Args:
        source (str): The path to the remote location.
        destination (str): The path to the local location. 

    Raises:
        None.
    """
    
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, source, destination):
        self._src = source
        self._dst = destination
        
        self._copy_state = False
        
    @abc.abstractmethod
    def copy(self):
        """Copies items from a remote source to a local destination.
        
        Args:
            None
        
        Returns:
            None
        
        Raises:
            :class:`CopyError`: Could not copy.
        """
        
        pass
    
    @property
    def was_copied(self):
        """Indicates that the item(s) were successfully copied.
        
        Args:
            None.
        
        Returns:
            (bln)
        
        Raises:
            :class:`CopyError`: Could not determine copy state.
        """
        
        return self._copy_state
    
class CopyBasic(_CopySourcer):
    """This class copies files from a source to a local directory. Used for Samba, CIFS,
        NFS, UNC, and local file copies. 
    
    Args:
        local source (str): The path to the source file.
        local destination (str): The local path the file will be copied to. 
        
    Raises:
        None.
    """
    
    def __init__(self, source, destination):
        super(CopyBasic, self).__init__(source, destination)
        
    def copy(self):
        """Copies files/directories from a remote source to a local destination. If a folder is
        used as the source a recurisve copy will be performed and the destination will be 
        recursively deleted.
        
        Args:
            None
        
        Returns:
            None
        
        Raises:
            :class:`CopyError`: Could not copy.
        """
        
        try:
            if isdir(self._src):
                if isdir(self._dst):
                    try:
                        shutil.rmtree(self._dst)
                    except shutil.Error as e:
                        raise CopyError("Could not remove all file in {0}.".format(self._dst))
                shutil.copytree(self._src, self._dst)
            elif isfile(self._src):
                dir_name = dirname(self._dst)
                if exists(dir_name):
                    try:
                        shutil.copy(self._src, self._dst)
                    except (OSError, shutil.Error, OSError, IOError) as e:
                        if e.errno != errno.EEXIST:
                            raise CopyError("Could not create {0}".format(self._dst))
                try: 
                    makedirs(dir_name)
                    shutil.copy(self._src, self._dst)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise CopyError("Could not create {0}".format(self._dst))
            else:
                raise CopyError("Could not determine the type of object at given path '{0}'!"
                                .format(self._src))
        except (IOError, OSError, WindowsError, shutil.Error) as e:
            raise CopyError("Could not copy files/directories from '{0}' to '{1}'!"
                            .format(self._src, self._dst))
            
        self._copy_state = True

#TODO: Implement the CopyFTP function. 

# class CopyFTP(_CopySourcer):
#     """Copy files/directories from a ftp server (source) to a local folder (destination).
#     
#     Args:
#         source (str): The path to the source file.
#         destination (str): The local path the file will be copied to. 
#         port (str): The port used to connect to the ftp server.
#         username (str): The username used to log into the ftp server.
#         password (str): The password for the username used to log into the ftp server.
#         
#     Raises:
#         None.
#     """
#     
#     def __init__(self, source, destination, port = 21, username, password):
#         super(CopyBasic, self).__init__(source, destination)
#         
#         self._username = username
#         self._password = password
#         self._port = port
#         self._ftp_host = self._source # Added for clarity. 
#         
#     def copy(self):
#         """Copies files/directories from a remote source to a local destination.
#         
#         Args:
#             None
#         
#         Returns:
#             None
#         
#         Raises:
#             :class:`CopyError`: Could not copy.
#         """
#         try:        # Create a connection
#             ftp = FTP(self._ftp_host, self._port, self._username, self._password)
#         except:
#             pass
        
        
        
        
#TODO: Implement thie CopyHTTP function. http://docs.python.org/2/library/httplib.html
class CopyHTTP(_CopySourcer):
    """Copy files/directories from a
    
    Args:
        source (str): The path to the source file.
        destination (str): The local path the file will be copied to. 
        
    Raises:
        None.
    """
    
    def __init__(self, name):
        self._name = name

# ===================================================================================================
# Exceptions
# ===================================================================================================
class CopyError(Exception):
    """Exception for errors in the copy_sourcer module.
    
    Args:
        msg (str): The reason for the copy error.
        
    """
    
    def __init__(self, msg):
        self.message = self.msg = msg
        
    def __str__(self):
        return "Copy Error: {0} ".format(self.msg)
                