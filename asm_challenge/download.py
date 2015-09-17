#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following line in the
entry_points section in setup.cfg:

    console_scripts =
        hello_world = asm_challenge.module:function

Then run `python setup.py install` which will install the command `hello_world`
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


from asm_challenge import __version__

__author__ = "Jose Luis Bellod Cisneros"
__copyright__ = "Jose Luis Bellod Cisneros"
__license__ = "none"

_logger = logging.getLogger(__name__)


def parse_args(args):
    """
    Parse command line parameters

    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser(
        description="Just a Hello World demonstration")
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='asm_challenge {ver}'.format(ver=__version__))
    return parser.parse_args(args)


def get_fastq_url_from_bioproject(bioproject, dir):
    """
    Get Fastq URK associated with Bioproject from SRA archive

    :param bioproject: ABioproject from SRA
    :return: table of FTP URLs
    """

    # base_url_old = 'http://www.ncbi.nlm.nih.gov/sra?'\
    #                'linkname=bioproject_sra_all&'\
    #                'from_uid='
    url = 'http://www.ncbi.nlm.nih.gov/biosample?'\
          'LinkName=bioproject_biosample_all&from_uid=%s'\
          '&format=text' % (bioproject)
    data = urllib.urlopen(url).read()
    m = re.findall(r"SRA: (.+)", data)
    for accession in m:
        _logger.info(accession)
        download_fastqSRA(accession, dir)


def download_fastq(accession, dir):
    """
    Download Fastq associated with Accession from ENA

    :param run_accession: Run Accession ID from ENA
    :return: True
    """
    # _logger.info('Downloading fastq %s' % accession)
    url = 'http://www.ebi.ac.uk/ena/data/warehouse/filereport?accession=' + \
        accession + '&result=read_run'
    data = urllib.urlopen(url).read()
    table = pd.read_csv(StringIO(data), sep='\t')
    # _logger.info(table)
    if table.index != []:
        _logger.info(url)
        if type(table['run_accession'][0]) == type('str'):
            for accession in table['run_accession']:
                _logger.info(accession)
                os.system("fastq-dump %s --outdir %s" % (accession, dir))
        else:
            _logger.warning(table['run_accession'][0])
            _logger.warning(type(table['run_accession'][0]))
            return None
    else:
        _logger.error(table.index)
        _logger.error(url)


def download_fastqSRA(accession, dir):
    """
    Download Fastq associated with Accession from ENA

    :param run_accession: Run Accession ID from ENA
    :return: True
    """

    url = 'http://www.ncbi.nlm.nih.gov/sra/?term='+accession+'&format=text'
    _logger.info(url)
    data = urllib.urlopen(url).read()
    # print(data)
    m = re.findall(r"Run #1: (\w+), ", data)
    for run in m:
        _logger.error(run)
        os.system("fastq-dump %s --outdir %s" % (run, dir))


def get_fastq_url_from_accession(accession):
    """
    Get Fastq URL associated with Accession from ENA

    :param accession: Accession ID from ENA
    :return: FTP URL
    """

    url = 'http://www.ebi.ac.uk/ena/data/warehouse/filereport?accession=' + \
        accession + '&result=read_run'

    data = urllib.urlopen(url).read()
    table = pd.read_csv(StringIO(data), sep='\t')
    if table.index != []:
        if type(table['fastq_ftp'][0]) == type('str'):
            # _logger.info(table['fastq_ftp'][0])
            return table['fastq_ftp'][0]
            if ';' in table['fastq_ftp'][0]:
                return table['fastq_ftp'][0].split(';')
            else:
                return table['fastq_ftp'][0]
        else:
            _logger.warning(table['fastq_ftp'][0])
            _logger.warning(type(table['fastq_ftp'][0]))
            return None


def download_species(species):

    # base for advanced search
    url_base = 'http://www.ebi.ac.uk/ena/data/warehouse/search?'
    for specie in species:
        d = Path('./data/%s' % specie["name"])
        dir = d.makedirs_p()
        url_query = 'query=\"tax_tree(' + str(specie["tax_id"]) + ')\"'
        url_result = '&result=sample'
        url_count = '&display=report'
        url_count = '&resultcount'
        url = url_base + url_query + url_result + url_count
        _logger.info(url)
        url_res = urllib.urlopen(url).read()
        _logger.info(url_res)
        n_samples = int(''.join(url_res.split('\n')[0].split()[-1].split(',')))
        _logger.info(n_samples)

        url_base = 'http://www.ebi.ac.uk/ena/data/warehouse/search?'
        url_query = 'query=\"tax_tree(' + str(specie["tax_id"]) + ')\"'
        url_result = '&result=sample'
        url_display = '&display=report'
        url_fields = '&fields=accession'
        url_limits = '&offset=1&length=' + str(n_samples)
        url = url_base + url_query + url_result + url_display + url_fields +\
            url_limits
        _logger.info(url)
        data = urllib.urlopen(url).read()
        table = pd.read_csv(StringIO(data), sep='\t')
        # table['ftp']= map(get_fastq_url_from_accession, table['accession'])
        # map(download_fastq, (table['accession'], dir)
        [download_fastq(accesion, dir) for accesion in table['accession']]
        _logger.info(table['accession'])


def main(args):
    args = parse_args(args)
    # http://www.ncbi.nlm.nih.gov/biosample?LinkName=bioproject_biosample_all&from_uid=295366&format=text
    bioproject_ids_lysteria = ['295367', '21211', '215355']
    bioproject_ids_salmonella = ['295366', '237212', '227458',
                                 '252015', '230403']
    bioprojects = [{'name': 'Lysteria', "id": bioproject_ids_lysteria},
                   {'name': 'Salmonella', "id": bioproject_ids_salmonella}]
    for project in bioprojects:
        species_path = project["name"]
        _logger.info(species_path)
        d = Path('./data/bioprojects/%s' % species_path)
        d.makedirs_p()
        for id in project["id"]:
            _logger.info(id)
            dir = './data/bioprojects/%s/PRJNA%s' % (species_path, id)
            dbio = Path(dir)
            dbio.makedirs_p()
            get_fastq_url_from_bioproject(id, dir)

    species = [{"name": 'Lysteria', "tax_id": 1639},
               {"name": 'Salmonella', "tax_id": 590}]
    download_species(species)
    _logger.info("Script ends here")


def run():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
