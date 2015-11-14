#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following line in the
entry_points section in setup.cfg:


Then run `python setup.py install` which will install the command `download`
inside your current environment.
Besides console scripts, the header (i.e. until _logger...) of this file can
also be used as template for Python modules.

Note: This skeleton file can be safely removed if not needed!
"""
from __future__ import division, print_function, absolute_import

import os
import sys
import re
import json
import argparse
import logging
import urllib
import pandas as pd
from StringIO import StringIO
from path import Path
from pprint import pprint as pp

from subprocess import call
from progressbar import Bar, Percentage, ProgressBar, ETA

from isolates.metadata import MetadataBioSample
from isolates.sequence import Sequence
from isolates import __version__

__author__ = "Jose Luis Bellod Cisneros"
__coauthor__ = "Martin C F Thomsen"
__copyright__ = "Jose Luis Bellod Cisneros"
__license__ = "none"

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='%(levelname)s:%(message)s'
)
_logger = logging.getLogger(__name__)


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
        version='isolates {ver}'.format(ver=__version__))

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
        '--version',
        action='version',
        version='isolates {ver}'.format(ver=__version__))

    parser.add_argument(
        '-a',
        nargs=1,
        metavar=('PATH'),
        help='Format: [PATH]\n' +
             'to file containing list of ACCESSION IDs, 1 per line\n' +
             'Name of the file is used to identify the isolates downloaded.'
    )
    parser.add_argument(
        '-m',
        nargs=1,
        type=argparse.FileType('r'),
        metavar=('METADATA'),
        default=None,
        help='JSON file with seed attributes and mandatory fields\n'
    )
    parser.add_argument(
        '-p',
        '--preserve',
        action="store_true",
        dest="preserve",
        default=False,
        help='preserve any existing SRA and fastq files\n'
    )
    # parser.add_argument(
    #     '-o',
    #     nargs=1,
    #     metavar=('organism'),
    #     help='Format: [ORGANISM]\n' +
    #          'to assign to all isolates'
    # )
    parser.add_argument(
        '-out',
        nargs=1,
        metavar=('OUTPUT'),
        required=True,
        help='Path to save isolates'
    )
    return parser.parse_args(args)


def download_fastq_from_list(accession_list, output, json, preserve=False):
    """
    Get Fastq from list of Ids

    :param accession_list: List of accessions
    :param dir: Output folder
    """

    metadata = []
    with open(accession_list, 'r') as f:
        d = Path('%s' % output)
        dir = d.makedirs_p()
        # Count samples in accession_list
        n_samples = sum(1 for l in f)
        f.seek(0)
        _logger.info("Number of samples to download: %s", n_samples)
        # Start progress bar
        pbar = ProgressBar(
            widgets = [ETA(), ' - ', Percentage(), ' : ', Bar()],
            maxval  = n_samples
        ).start()
        pbar.update(0)
        for i, l in enumerate(f):
            accession = l.strip()
            if accession == '': continue
            if json is None:
                m = MetadataBioSample(accession)
            else:
                m = MetadataBioSample(accession, json)
            m.update_attributes()
            m.update_biosample_attributes()
            if m.valid_metadata():
                try:
                    s = Sequence(m.accession, dir)
                    s.download_fastq(preserve)
                    if not s.error:
                        m.metadata["file_names"] = ' '.join(
                            [os.path.basename(sf).replace(' ','_')
                                for sf in s.files
                                if not os.path.basename(sf) == 'meta.json']
                            )
                        m.save_metadata(s.dir)
                except ValueError, e:
                    _logger.error(e)
            else:
                s = Sequence(accession, dir)
                message = 'Metadata not valid: %s' % m.url
                _logger.error(message)
                s.errors = message
            pbar.update(i)
        pbar.finish()
        errors = s.errors.items()
        if errors != []:
            _logger.info("The following accessions were not downloaded!")
            for i in errors:
                _logger.info('Accession %s [%s]', i[0], i[1])
        else:
            _logger.info("All accessions downloaded succesfully!")


def download_accession_list():
    args = parse_args_accessions(sys.argv[1:])
    if args.a is not None:
        _logger.info('Good!')
        if args.m is not None:
            try:
                default = json.load(args.m[0])
            except ValueError as e:
                print("ERROR: Json file has the wrong format!\n", e)
                exit()
        else:
            default = None
        download_fastq_from_list(args.a[0], args.out[0], default, args.preserve)
    else:
        print('Usage: -a PATH -o ORGANISM -out PATH [-m JSON]')


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
