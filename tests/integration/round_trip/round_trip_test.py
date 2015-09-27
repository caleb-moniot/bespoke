"""
.. module:: round_trip_test
   :platform: Linux, Windows
   :synopsis: System integration tests for the Bespoke application. (End-to-end)
   :license: BSD, see LICENSE for more details.

.. moduleauthor:: Ryan Gard <ryan.a.gard@outlook.com>
"""

# ===================================================================================================
# Imports
# ===================================================================================================
from unittest import TestCase, skipIf
from os.path import join
from bespoke import main

# ===================================================================================================
# Globals
# ===================================================================================================
SKIP_EVERYTHING = False
CONFIGS = r'configs/'
XSD_PATH = r'../../../src/bespoke/xsd/'


# ===================================================================================================
# Classes
# ===================================================================================================
class FakeArgs(object):
    """A class for wrapping arguments for ArgParse.

    Args:
        **kwargs ({str:str}): An arbitrary set of keyword arguments that result in object properties.
            The keys are the property name with the values being the property data.

    Raises:
        :class:`ConfigError`: The config file or XSD file were not found.
    """

    def __init__(self, **kwargs):
        for key in kwargs:
            self.__dict__[key] = kwargs[key]


# ===================================================================================================
# Tests
# ===================================================================================================
class RoundTrip(TestCase):
    """This class contains end-to-end tests for basic functionality."""

    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test01_remote_script_no_install(self):
        """Execute a test script on a remote SUT."""

        # Init
        global_cfg = "{}test01/global.xml".format(CONFIGS)
        test_run_cfg = 'test_run.xml'
        args = FakeArgs(xsd_path=XSD_PATH,
                        global_config=global_cfg,
                        test_run_config=test_run_cfg,
                        log_path='bespoke.log')

        # Test
        self.assertEquals(main(args), 0, 'Test run failed!')
