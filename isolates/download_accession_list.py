#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following line in the
entry_points section in setup.cfg:

    console_scripts =
        download = asm_challenge.download:run

Then run `python setup.py install` which will install the command `download`
inside your current environment.
Besides console scripts, the header (i.e. until _logger...) of this file can
also be used as template for Python modules.

Note: This skeleton file can be safely removed if not needed!
"""
from __future__ import division, print_function, absolute_import

import argparse
import sys
import logging
import pandas as pd
import urllib
from StringIO import StringIO
from path import Path
import os
import re
import json

from pprint import pprint as pp

from subprocess import call
from progressbar import Bar, Percentage, ProgressBar, ETA

from isolates.metadata import Metadata
from isolates.sequence import Sequence
from isolates import __version__

__author__ = "Jose Luis Bellod Cisneros"
__copyright__ = "Jose Luis Bellod Cisneros"
__license__ = "none"

_logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='%(levelname)s:%(message)s'
)


def parse_args_bioproject(args):
    """
    Parse command line parameters

    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser(
        description="Download script of isolates from" +
                    "ENA taxonomy or Accession list")
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='asm_challenge {ver}'.format(ver=__version__))

    parser.add_argument(
        '-b',
        nargs=3,
        metavar=('BIOPROJECTID', 'ORGANISM', 'PATH'),
        help='Format: [BIOPROJECTID] [ORGANISM] [PATH]\n' +
             '[BIOPROJECTID] if unknown insert a unique ID\n' +
             '[PATH] to file containing list of ACCESSION IDs, 1 per line\n' +
             'Name of the file is used to identify the isolates downloaded.'
    )
    parser.add_argument(
        '-out',
        nargs=1,
        metavar=('OUTPUT'),
        required=True,
        help='Path to save isolates'
    )
    return parser.parse_args(args)


def parse_args_accessions(args):
    """
    Parse command line parameters

    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser(
        description="Download script of isolates from" +
                    "ENA taxonomy or Accession list")
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='asm_challenge {ver}'.format(ver=__version__))

    parser.add_argument(
        '-a',
        nargs=1,
        metavar=('PATH'),
        help='Format: [PATH]\n' +
             'to file containing list of ACCESSION IDs, 1 per line\n' +
             'Name of the file is used to identify the isolates downloaded.'
    )
    parser.add_argument(
        '-o',
        nargs=1,
        metavar=('organism'),
        help='Format: [ORGANISM]\n' +
             'to assign to all isolates'
    )
    parser.add_argument(
        '-out',
        nargs=1,
        metavar=('OUTPUT'),
        required=True,
        help='Path to save isolates'
    )
    return parser.parse_args(args)


def download_fastq_from_list(accession_list, organism, output):
    """
    Get Fastq from list of Ids

    :param accession_list: List of accessions
    :param dir: Output folder
    """

    metadata = []
    f = open(accession_list, 'r')
    line = 0
    n_samples = len([aux for aux in f])
    f = open(accession_list, 'r')
    d = Path('%s/%s' % (output, organism))
    dir = d.makedirs_p()
    _logger.info("Isolates to be downloaded: %s", n_samples)
    pbar = ProgressBar(
        widgets=[ETA(), Percentage(), Bar()],
        maxval=n_samples
    ).start()
    i = 0
    for accession in f:
        m = Metadata({
            'pre_assembled': 'no',
            'sample_type': 'isolate',
            'sample_name': accession.strip(),
            'organism': organism,
            'pathogenic': 'yes',
            'usage_restrictions': 'public',
            'usage_delay': '0'
            }, accession)
        m.update_attributes()
        if m.valid_metadata():
            s = Sequence(accession, dir)
            s.download_fastq()
            if not s.error:
                m.metadata["file_names"] = ''.join(s.files)
                m.save_metadata(s.dir)
        else:
            _logger.error('Metadata not valid: %s', m.url)
        pbar.update(i)
        i += 1
    pbar.finish()
    errors = s.errors.items()
    if errors != []:
        _logger.info("The following accessions were not downloaded!")
        for i in errors:
            _logger.info(i[0])
    else:
        _logger.info("All accessions downloaded succesfully!")


def download_accession_list():
    # logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    args = parse_args_accessions(sys.argv[1:])
    if args.a is not None and args.o is not None:
        _logger.info('Good!')
        download_fastq_from_list(args.a[0], args.o[0], args.out[0])
    else:
        _logger.error('Usage: [-a PATH] [-o ORGANISM]')


def download_bioproject():
    # logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    args = parse_args_bioproject(sys.argv[1:])
    if args.b is not None:
        _logger.info('Good!')
        download_fastq_from_bioproject()
    else:
        _logger.error('Usage: [-b BIOPROJECTID ORGANISM PATH]')

if __name__ == "__main__":
    download_accession_list()
