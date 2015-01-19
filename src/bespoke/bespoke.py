#!/usr/bin/env python
"""
bespoke_server -- shortdesc

bespoke_server is a description

It defines classes_and_methods

@author:     Ryan Gard & Caleb Moniot
        
@copyright:  2014 Fancy Lads Software LLC. All rights reserved.
        
@license:    BSD
"""

#===================================================================================================
# Imports
#===================================================================================================
import sys
from os import getcwd
from socket import gethostname
from os.path import abspath, basename, join
from argparse import ArgumentParser
from runtime import ExecuteTestRun, ExecutionError

#TODO: Add the ability to override each config with another config.

#===================================================================================================
# Globals
#===================================================================================================
__version__ = 0.1
XSD_PATH_DEFAULT = 'xsd'
CWD = getcwd()

#===================================================================================================
# Functions
#===================================================================================================
def cli_parser():
    """Command line options."""

    program_name = basename(sys.argv[0])

    # Setup argument parser
    parser = ArgumentParser()
    
    parser.add_argument("-g", 
                        "--global-config", 
                        dest="global_config", 
                        required=True, 
                        help="Path to the GlobalConfig.xml")
    
    parser.add_argument("-r", 
                        "--test-run-config", 
                        dest="test_run_config", 
                        required=True, 
                        help="Path to the TestRunConfig.xml")
    
    parser.add_argument('-V', 
                        '--version', 
                        action='version', 
                        version=__version__)
    
    parser.add_argument('-X',
                        '--xsd-path',
                        dest='xsd_path',
                        default=join(CWD, XSD_PATH_DEFAULT),
                        help="Path to the Bespoke xsd directory")
    
    # Process arguments
    args = parser.parse_args()
    return args  

def display_error(extended_message, exception, exit_code=1):
    """Load the global config for parsing.
    
    Args:
        extended_message |str| = A message providing more context for the exception. 
        exception |Exception| = The exception who's message is to be displayed.
        exit_code |int| = The exit code of the exception.
    
    Returns:
        |int| = The exit_code passed to the system.
        
    Raises:
         None
    """
    
    print("{0} - {1}".format(extended_message, str(exception)))
    return exit_code
    
#===================================================================================================
# Main
#===================================================================================================
def main(args):
    exit_code = 0
    
    try: 
        test_run = ExecuteTestRun(CWD, args.xsd_path, args.global_config, args.test_run_config)
        test_run.execute_test_run()
    except ExecutionError as e:
        exit_code = display_error("Failed to execute test run.", e)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main(cli_parser()))