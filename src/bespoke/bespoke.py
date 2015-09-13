#!/usr/bin/env python
"""
bespoke_server -- shortdesc

bespoke_server is a description

It defines classes_and_methods

@author:     Ryan Gard & Caleb Moniot
        
@copyright:  2014 Fancy Lads Software LLC. All rights reserved.
        
@license:    BSD
"""

# ===================================================================================================
# Imports
# ===================================================================================================
import sys
import logging
from os import getcwd
from os.path import join
from argparse import ArgumentParser
from runtime import ExecuteTestRun, ExecutionError

# TODO: Add the ability to override each config with another config.

# ===================================================================================================
# Globals
# ===================================================================================================
__version__ = 0.1
XSD_PATH_DEFAULT = 'xsd'
CWD = getcwd()
global_logger = None


# ===================================================================================================
# Functions
# ===================================================================================================
def cli_parser():
    """Command line options.

    Args:
        None

    Returns:
        |args| = args object.

    Raises:
         None
    """
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

    parser.add_argument('-l',
                        '--log-path',
                        dest='log_path',
                        default=join(CWD, 'bespoke.log'),
                        help="Path to the Bespoke log file.")

    # Process arguments
    args = parser.parse_args()

    return args


def set_logging(log_file_path, log_level='DEBUG'):
    """Configure logging for the bespoke application.

    Args:
        log_file_path |str| = Absolute path to the log file. Include file name.
        log_level     |str| = Log level. Accepted values are:
            'CRITICAL'
            'ERROR'
            'WARNING'
            'INFO'
            'DEBUG'

    Returns:
        |logger|

    Raises:
        :class:`ExecutionError`
    """

    # TODO: Not sure what exceptions are raised. Create a test to evaluate possible exceptions.
    logger = logging.getLogger('bespoke')
    fh = logging.FileHandler(log_file_path)
    ch = logging.StreamHandler()

    if log_level == 'CRITICAL':
        logger.setLevel(logging.CRITICAL)
        fh.setLevel(logging.CRITICAL)
        ch.setLevel(logging.CRITICAL)
    elif log_level == 'ERROR':
        logger.setLevel(logging.ERROR)
        fh.setLevel(logging.ERROR)
        ch.setLevel(logging.ERROR)
    elif log_level == 'WARNING':
        logger.setLevel(logging.WARNING)
        fh.setLevel(logging.WARNING)
        ch.setLevel(logging.WARNING)
    elif log_level == 'INFO':
        logger.setLevel(logging.INFO)
        fh.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)
    elif log_level == 'DEBUG':
        # TODO: (1/2) In the future add a different formater for the debug level so that we can determine what module logged the message.
        # TODO: (2/2) This may nessececate the a logger for each level instead of the current global.
        logger.setLevel(logging.DEBUG)
        fh.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    else:
        raise ExecutionError("Invalid logging level specified!")

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # TODO: Implement the logger.
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


# ===================================================================================================
# Main
# ===================================================================================================
def main(args):

    try:
        logger = set_logging(args.log_path, 'DEBUG')
        logger.info('Starting test run...')
        test_run = ExecuteTestRun(CWD, args.xsd_path, args.global_config, args.test_run_config)
        test_run.execute_test_run()
    except ExecutionError as e:
        logger.error("Failed to execute test run: {0}".format(e.msg))
        # TODO: Update after exit codes are finalized.
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main(cli_parser()))
