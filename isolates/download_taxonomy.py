#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following line in the
entry_points section in setup.cfg:

    console_scripts = download-taxonomy -t ORGANISM TAXID -output OUTPUT

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


def parse_args_taxonomy(args):
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
        '-t',
        nargs=2,
        metavar=('TAXID', 'ORGANISM'),
        help='Tax ID from ENA data archive and organism associated'
    )
    parser.add_argument(
        '-output',
        nargs=1,
        metavar=('OUTPUT'),
        required=True,
        help='Path to save isolates'
    )
    return parser.parse_args(args)


def download_species(species, output):
    """
    Download FASTQ files based on ENA Tax ID

    :param species: {"name": SPECIES_NAME, "tax_id": ENA_TAX_ID}
    :param output: PATH
    :return:
    """
    # base for advanced search
    url_base = 'http://www.ebi.ac.uk/ena/data/warehouse/search?'
    for specie in species:
        d = Path('%s/%s' % (output, specie["name"]))
        dir = d.makedirs_p()
        url_query = 'query=\"tax_tree(' + str(specie["tax_id"]) + ')\"'
        url_result = '&result=sample'
        url_count = '&display=report'
        url_count = '&resultcount'
        url = url_base + url_query + url_result + url_count
        url_res = urllib.urlopen(url).read()
        try:
            n_samples = int(''.join(
                url_res.split('\n')[0].split()[-1].split(',')))
        except Exception as e:
            _logger.exception(e)
            quit()
        _logger.info("Isolates to be downloaded: " + str(n_samples))
        if n_samples == 0:
            _logger.exception("This Tax id has no isolates associated")
        url_base = 'http://www.ebi.ac.uk/ena/data/warehouse/search?'
        url_query = 'query=\"tax_tree(' + str(specie["tax_id"]) + ')\"'
        url_result = '&result=sample'
        url_display = '&display=report'
        url_fields = '&fields=accession'
        url_limits = '&offset=1&length=' + str(n_samples)
        url = url_base + url_query + url_result + url_display + url_fields +\
            url_limits
        data = urllib.urlopen(url).read()
        table = pd.read_csv(StringIO(data), sep='\t')

        error_accession_list = []
        pbar = ProgressBar(
            widgets=[ETA(), Percentage(), Bar()],
            maxval=len(table['accession'])
        ).start()
        i = 0
        for accession in table['accession']:
            m = Metadata({
                'pre_assembled': 'no',
                'sample_type': 'isolate',
                # 'organism: fld[head.index('ScientificName')]
                'pathogenic': 'yes',
                'usage_restrictions': 'public',
                'usage_delay': '0'
                }, accession)
            m.update_attributes()
            if m.valid_metadata():
                s = Sequence(accession, dir)
                s.download_fastq()
                if accession not in s.errors:
                    m.metadata.files = ''.join(s.files)
                # error_accession_list.append(download_fastq(accession, dir))
            else:
                _logger.error('Metadata not valid: %s', accession)
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


def download_taxonomy():
    """
    Example input data

    :param args: -t TAXID ORGANISM
    :return:
    """

    args = parse_args_taxonomy(sys.argv[1:])
    if args.t is not None:
        download_species(
            [{"name": args.t[0], "tax_id": args.t[1]}],
            args.output[0]
        )
    else:
        _logger.error('Usage: [-t TAXID ORGANISM]')

if __name__ == "__main__":
    download_taxonomy()
