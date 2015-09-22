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

from asm_challenge import __version__

__author__ = "Jose Luis Bellod Cisneros"
__copyright__ = "Jose Luis Bellod Cisneros"
__license__ = "none"

_logger = logging.getLogger(__name__)


bioproject_files = {
    "295366": "./input/295366.txt",
    "215355": "./input/215355.txt",
    "295367": "./input/295367.txt",
    "237212": "./input/237212.txt",
    "227458": "./input/227458.txt",
    "252015": "./input/252015.txt",
    "230403": "./input/230403.txt"
}

bioproject_organism = {
    "295366": "Salmonella Enteritidis",
    "215355": "Listeria monocytogenes",
    "295367": "Listeria monocytogenes",
    "237212": "Salmonella Enteritidis",
    "227458": "Salmonella Enteritidis",
    "252015": "Salmonella Enteritidis",
    "230403": "Salmonella Enteritidis"
}

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

def get_metadata(accession, bioID):

    metadata = {
        "sample_name": accession,
        "group_name": "",
        "file_names": "",
        "sequencing_platform": "Illumina",
        "sequencing_type": "single",
        "pre_assembled": "no",
        "sample_type": "isolate",
        "organism": bioproject_organism[bioID],
        "strain": "",
        "subtype": "",
        "country": "",
        "region": "",
        "city": "",
        "zip_code": "",
        "longitude": "",
        "latitude": "",
        "location_note": "",
        "isolation_source": "other",
        "source_note": "",
        "pathogenic": "unknown",
        "pathogenicity_note": "",
        "collection_date": "",
        "collected_by": "",
        "usage_restrictions": "private",
        "release_date": "",
        "email_address": "",
        "notes": "",
        "upload_dir": 1,
        "batch": "true"
    }
    isolation_source = ["human", "water", "food", "animal", "laboratory", "other"]
    url = 'http://www.ncbi.nlm.nih.gov/sra/?term='+ accession +'&format=text'
    data = urllib.urlopen(url).read()
    m = re.findall(r"Sample Attributes: (.+)\n", data)
    _logger.info(m)
    for answer in m:
        for attributes in answer.split(';'):
            stat = attributes.split('=')
            _logger.info(stat)
            if stat[0].strip() == 'geo_loc_name' and ":" in stat[1]:
                metadata["country"] = stat[1].split(":")[0]
                metadata["region"] = stat[1].split(":")[1]
            elif stat[0].strip() == 'geo_loc_name':
                metadata["country"] = stat[1]
            if stat[0].strip() in metadata:
                if stat[0].strip() == 'isolation_source':
                    if stat[1] not in isolation_source:
                        metadata[stat[0].strip()] = 'other'
                        metadata['source_note'] = stat[1]
                elif stat[0].strip() == 'BioSample':
                    metadata['notes'] = metadata['notes'] + ' BioSample=' + stat[1] + ', '
                # elif stat[0].strip() == 'run':
                #     metadata['notes'] = metadata['notes'] + ' run=' + stat[1]  + ', '
                else:
                    metadata[stat[0].strip()] = stat[1]
        # metadata['file_names'] = '%s_1.fastq.gz %s_2.fastq.gz' % (accession.strip('\n'), accession.strip('\n'))
        metadata['file_names'] = '%s.fastq' % (accession.strip('\n'))
        metadata['notes'] = metadata['notes'] + ' run=' + accession  + ', '
        metadata['sample_name'] = metadata['strain']
    return metadata


def get_fastq_from_list(bioproject, dir):
    """
    Get Fastq from list of Ids

    :param bioproject: ABioproject from SRA
    :return: table of FTP URLs
    """

    metadata = []
    f = open(bioproject_files[bioproject], 'r')
    line = 0
    total = len([aux for aux in f])
    _logger.error(total)
    f = open(bioproject_files[bioproject], 'r')
    for accession in f:
        accession = accession.strip()
        _logger.info(accession)
        metadata = get_metadata(accession, bioproject)
        _logger.info(metadata)

        if line/total < 0.5:
            FOLDER = dir + '_batch_1/' + str(line) + '/'
        else:
            FOLDER = dir + '_batch_2/' + str(line) + '/'
        dbio = Path(FOLDER)
        dbio.makedirs_p()
        if not os.path.exists(dir + '/' + accession + '.fastq'):
            _logger.info(accession.strip() + ' new')
            _logger.info("%s" % (FOLDER))
            os.system("fastq-dump %s --split-3 --gzip --outdir %s"
                      % (accession.strip(), FOLDER))
        else:
            _logger.info(accession + ' moving...')
            d = Path(dir + '_batch_1/' + accession + '.fastq')
            d.move(ddir + '_batch_1/' + str(line))
        f = open(FOLDER + 'meta.json', 'w')
        _logger.info(json.dumps(metadata))
        f.write(json.dumps(metadata))
        f.close()

        line += 1
    return metadata


def get_metadata_from_list(bioproject, dir):
    """
    Get Fastq from list of Ids

    :param bioproject: ABioproject from SRA
    :return: table of FTP URLs
    """

    metadata = []
    f = open(bioproject_files[bioproject], 'r')
    line = 0
    for accession in f:
        accession = accession.strip()
        _logger.info(accession)
        metadata = get_metadata(accession, bioproject)
        _logger.info(metadata)
        dbio = Path(dir + '/' + str(line))
        dbio.makedirs_p()
        f = open(dir + '/' + str(line) + '/' + 'meta.json', 'w')
        _logger.info(json.dumps(metadata))
        f.write(json.dumps(metadata))
        f.close()
        line += 1
    return metadata


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
    bioproject_ids_lysteria = ['295367',
                            #    '21211',
                            #   '215355'
                               ]
    bioproject_ids_salmonella = ['295366',
                                #  '237212',
                                #  '227458',
                                #  '252015',
                                #  '230403'
                                 ]
    bioprojects = [{'name': 'Lysteria', "id": bioproject_ids_lysteria},
                   {'name': 'Salmonella', "id": bioproject_ids_salmonella}]
    for project in bioprojects:
        species_path = project["name"]
        _logger.info(species_path)
        d = Path('./data2/bioprojects/%s' % species_path)
        d.makedirs_p()
        for id in project["id"]:
            _logger.info(id)
            dir = './data2/bioprojects/%s/PRJNA%s' % (species_path, id)
            dbio = Path(dir)
            dbio.makedirs_p()
            # get_fastq_url_from_bioproject(id, dir)
            get_metadata_from_list(id, dir)
            #get_fastq_from_list(id, dir)

    species = [{"name": 'Lysteria', "tax_id": 1639},
               {"name": 'Salmonella', "tax_id": 590}]
    # download_species(species)
    _logger.info("Script ends here")


def run():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
