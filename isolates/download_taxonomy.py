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

import sys
import os
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

from isolates import __version__
import isolates.metadata
import isolates.sequence

MetadataBioSample = isolates.metadata.MetadataBioSample
Sequence = isolates.sequence.Sequence

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
        nargs=1,
        metavar=('TAXID'),
        help='Tax ID from ENA data archive'
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
        '-out',
        nargs=1,
        metavar=('OUTPUT'),
        required=True,
        help='Path to save isolates'
    )
    return parser.parse_args(args)


def download_species(taxid, output, json):
    """
    Download FASTQ files based on ENA Tax ID

    :param species: {"name": SPECIES_NAME, "tax_id": ENA_TAX_ID}
    :param output: PATH
    :return:
    """
    # base for advanced search
    url_base = 'http://www.ebi.ac.uk/ena/data/warehouse/search?'
    d = Path('%s' % output)
    dir = d.makedirs_p()
    url_query = 'query=\"tax_tree(' + str(taxid) + ')\"'
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
    url_query = 'query=\"tax_tree(' + str(taxid) + ')\"'
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
        if json is None:
            m = MetadataBioSample(accession)
        else:
            m = MetadataBioSample(accession, json)
        m.update_attributes()
        m.update_biosample_attributes()
        if m.valid_metadata():
            try:
                s = Sequence(m.accession, dir)
                s.download_fastq()
                if not s.error:
                    m.metadata["file_names"] = ' '.join(
                        [os.path.basename(sf).replace(' ','_')
                            for sf in s.files
                            if not os.path.basename(sf) == 'meta.json']
                        )
                    m.save_metadata(s.dir)
            except ValueError, e:
                _logger.error('%s:%s', accession.strip(), e)
        else:
            s = Sequence(accession, dir)
            message = 'Metadata not valid: %s' % m.url
            _logger.error(message)
            s.errors = message
            # _logger.error('Metadata not valid: %s', m.accession)
            # _logger.error('Metadata not valid: %s', m.url)
            # _logger.error('%s', '= ,'.join(
            #         ["%s = %s" % (att, str(m.metadata[att]))
            #             for att in m.metadata]))
        pbar.update(i)
        i += 1
    pbar.finish()
    errors = s.errors.items()
    if errors != []:
        _logger.info("The following accessions were not downloaded!")
        for i in errors:
            _logger.info('Accession %s [%s]', i[0], i[1])
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
        if args.m is not None:
            try:
                default = json.load(args.m[0])
            except ValueError as e:
                print("ERROR: Json file has the wrong format!\n", e)
                exit()
        else:
            default = None
        download_species(args.t[0], args.out[0], default)
    else:
        _logger.error('Usage: -t TAXID ORGANISM')

if __name__ == "__main__":
    download_taxonomy()
