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
from unittest import TestCase, skip
from bespoke import main

# ===================================================================================================
# Globals
# ===================================================================================================
SKIP_EVERYTHING = False
CONFIGS = r'configs/'


# ===================================================================================================
# Tests
# ===================================================================================================
class HappyPath(TestCase):
    """This class contains end-to-end tests for basic functionality."""

    @skipIf(SKIP_EVERYTHING, 'Skip if we are creating/modifying tests!')
    def test01_remote_script_no_install(self):
        """Execute a test script on a remote SUT."""

        test_obj = _ConfigAccessor(SHARED_CONFIGS + r'_config/happy_path.xml',
                                   SHARED_CONFIGS + r'_config/happy_path.xsd')

        test_obj.parse_config()

        self.assertIsInstance(test_obj, _Config)