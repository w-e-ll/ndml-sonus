#!/bin/env python
"""
Module to parse different reports from Sonus
"""
import os
import sys
import traceback

from optparse import OptionParser

from ndml_sonus.scripts import sonus_logging

# Imports needed for the dynamic instantiation done by new function
from ndml_sonus.scripts.second_step import *
from ndml_sonus.scripts.gsx_parsers import *
from ndml_sonus.scripts.psx_parsers import *
from ndml_sonus.scripts.sgx_parsers import *
from ndml_sonus.scripts.common_exceptions import *

from ndml_sonus.lib.ndml_utils_tgw import Config


class InstantiationException(Exception):
    pass


class ParseException(Exception):
    pass


def new(class_name, *args, **kwargs):
    """
    Returns an instance of class: class_name (string).
    Raises NoSuchClassException if class_name does not match
    a defined class in the local scope.
    """
    try:
        the_class = None
        for part in class_name.split('.'):
            if the_class is None:
                the_class = globals()[part]
            else:
                the_class = the_class.__dict__[part]
                
        return the_class(*args, **kwargs)
    except KeyError:
        raise InstantiationException('no such class: %s' % class_name)
    except TypeError as e:
        raise InstantiationException('%s: TypeError: %s' % (class_name, str(e)))


class Arguments:
    def __init__(self):
        self.p = OptionParser(usage='usage: % prog [options]')
        self.p.add_option('-c', '--config', action='store',  help='config file for the script', type='string', dest='conf_file')
        self.p.add_option('-o', '--host',   action='append', help='host from which to extract the reports, option can be repeated for multiple hosts. If not specified: all hosts for the specified report(s).', type='string', default=[])
        self.p.add_option('-r', '--report', action='append', help='reports to extract from the host(s), can be repeated. If not specified, extracts all reports in the active_reports config file variable.', type='string', default=[])

    def get_arguments(self):
        (self.opt, self.args) = self.p.parse_args()
        
        if len(self.args) > 0:
            self.p.error('incorrect number of arguments (remains: %s)' % str(self.args))
            
        if not self.opt.conf_file:
            self.p.error('please specify the configuration file (--config)')
        
    def __getattr__(self, attr):
        return getattr(self.opt, attr)


def process_report(report, host, conf):
    try:
        conf.log.debug('starting parsing for report %s' % report.name)
        parser = new(report.parser, conf, host, report)
        parser.export()
        # the parsing was successful so move the file from tmp dir to csv dir
        try:
            # remove the old csv file first
            os.unlink(parser.output_filename)
            # conf.log.debug('deleted the old csv for report %s' % report.name)
        except:
            pass
        os.rename(parser.tmp_output_filename, parser.output_filename)
        # conf.log.debug('moved %s to %s' % (parser.tmp_output_filename, parser.output_filename))
    except ParseException as e:
        if conf.devmode:
            raise e
        else:
            conf.log.critical('got parsing exception, skipping')
            conf.log.critical(traceback.format_exception(*sys.exc_info()))
    except Exception as e:
        conf.log.critical('got unexpected exception type', e)
        conf.log.critical(traceback.format_exception(*sys.exc_info()))


def main():
    args = Arguments()
    args.get_arguments()

    conf = Config(args.conf_file, 'parser')
    
    # If only one report specified, create pid file specific to this report
    # so other instances of the same script are allowed to run in parallel 
    # for other reports.
    if len(args.report) == 1:
        conf.makePid(label=args.report[0])
    else:
        conf.makePid()
        
    conf.log.info('Report parsing starting')
    
    sonus_logging.log = conf.log

    try:
        for report in conf.iter_reports(args.report):
            for host in report.iter_hosts(args.host):
                process_report(report, host, conf)
    finally:
        conf.delPid()
        conf.log.info('All done')


if __name__ == '__main__':
    main()
