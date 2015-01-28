"""
.. module:: util
   :platform: Linux, Windows
   :synopsis: This module contains useful functions for use within the Bespoke application.
   :license: BSD, see LICENSE for more details.

.. moduleauthor:: Ryan Gard <ryan.a.gard@outlook.com>
"""
__version__ = 0.2

#===================================================================================================
# Imports
#===================================================================================================
import time
from collections import Counter
from itertools import chain
#===================================================================================================
# Decorators
#===================================================================================================
class retry(object):
    """This decorator will allow retry of functions/methods that RETURN values with wait and retry
    timeout.
    
    Args:
        tries (int): The number of tries.
        exceptions (exp): The exception(s) to catch and retry.
        delay (int): The number of seconds between retries.
    """
    
    default_exceptions = (Exception,)
    def __init__(self, tries, exceptions=None, delay=0):
        self.tries = tries
        if exceptions is None:
            exceptions = retry.default_exceptions
        self.exceptions =  exceptions
        self.delay = delay

    def __call__(self, f):
        def fn(*args, **kwargs):
            exception = None
            for _ in range(self.tries):
                try:
                    return f(*args, **kwargs)
                except self.exceptions, e:
                    #print "Retry, exception: "+str(e)
                    time.sleep(self.delay)
                    exception = e
            #if no success after tries, raise last exception
            raise exception
        return fn
    
#===================================================================================================
# Functions
#===================================================================================================
def nop(*args, **kwargs):
    """Classic No Op for just always returning true.
        
    Args:
        None.
    
    Returns:
        (True): Always.
    
    Raises:
        None.
    """
    
    return True

def unix_style_path(path):
    """Convert Windows path to a Unix style path. (Replace "\" with "/")
        
    Args:
        None.
    
    Returns:
        (str) = A path with Unix style separators.
    
    Raises:
        None.
    """
    
    return path.replace('\\', '/')

def duplicate_dictionary_keys(dicts):
    """Find the duplicate keys in an iterable of dictionaries.
        
    Args:
        dicts ([dict]) = An iterable of dictionaries.
    
    Returns:
        ([obj]) = A list of duplicate keys.
    
    Raises:
        None.
    """
    
    merged_keys = [j for j in chain.from_iterable([i.keys() for i in dicts])]
    
    return [x for x, y in Counter(merged_keys).items() if y > 1]

def merge_dictionaries(dicts, fail_on_duplicates=False):
    """Merge multiple dictionaries together.
        
    Args:
        dicts ([dict]) = An iterable of dictionaries.
        fail_on_duplicates (bool) = A flag indicating if duplicate keys are found in the merged
            dictionary.
    
    Returns:
        (dict) = A merged dictionary.
    
    Raises:
        KeyError = A duplicate key was found in the merged dictionary. (Only raised if 
            fail_on_duplicates is set.)
    """
    
    if fail_on_duplicates:
        duplicates = duplicate_dictionary_keys(dicts)
        if len(duplicates) > 0:
            raise KeyError('The dictionaries have duplicate keys! {0}'.format(duplicates))
        
    return {k:v for d in dicts for k, v in d.iteritems()}
