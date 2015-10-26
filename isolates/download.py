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
        nargs=3,
        metavar=('BIOPROJECTID', 'ORGANISM', 'PATH'),
        help='Format: [BIOPROJECTID] [ORGANISM] [PATH]\n' +
             '[BIOPROJECTID] if unknown insert a unique ID\n' +
             '[PATH] to file containing list of ACCESSION IDs, 1 per line\n' +
             'Name of the file is used to identify the isolates downloaded.'
    )
    parser.add_argument(
        '-output',
        nargs=1,
        metavar=('OUTPUT'),
        required=True,
        help='Path to save isolates'
    )
    return parser.parse_args(args)


def get_fastq_url_from_bioproject(bioproject, dir):
    """
    Get Fastq URL associated with Bioproject from SRA archive

    :param bioproject: Bioproject from SRA
    :param dir: Output folder
    :return: table of FTP URLs
    """

    url = 'http://www.ncbi.nlm.nih.gov/biosample?'\
          'LinkName=bioproject_biosample_all&from_uid=%s'\
          '&format=text' % (bioproject)
    data = urllib.urlopen(url).read()
    m = re.findall(r"SRA: (.+)", data)
    for accession in m:
        _logger.info(accession)
        download_fastqSRA(accession, dir)


# def get_metadata(accession, bioID):
#
#     metadata = {
#         "sample_name": accession,
#         "group_name": "",
#         "file_names": "",
#         "sequencing_platform": "",
#         "sequencing_type": "",
#         "pre_assembled": "",
#         "sample_type": "",
#         "organism": "",
#         "strain": "",
#         "subtype": "",
#         "country": "",
#         "region": "",
#         "city": "",
#         "zip_code": "",
#         "longitude": "",
#         "latitude": "",
#         "location_note": "",
#         "isolation_source": "",
#         "source_note": "",
#         "pathogenic": "",
#         "pathogenicity_note": "",
#         "collection_date": "",
#         "collected_by": "",
#         "usage_restrictions": "",
#         "release_date": "",
#         "email_address": "",
#         "notes": "",
#         "batch": "true"
#     }
#     url = 'http://www.ncbi.nlm.nih.gov/sra/?term=' + accession
#           + '&format=text'
#     data = urllib.urlopen(url).read()
#     match = re.findall(r"Sample Attributes: (.+)\n", data)
#     _logger.info(m)
#     for answer in match:
#         for attributes in answer.split(';'):
#             stat = attributes.split('=')
#             att = stat[0].strip('/ ').lower().replace("'", "")
#             val = stat[1].strip('" ').replace("'", "`")
#             _logger.info(stat)
#             if att == 'geo_loc_name' and ":" in stat[1]:
#                 metadata["country"] = val.split(":")[0]
#                 metadata["region"] = val.split(":")[1]
#             elif att == 'geo_loc_name':
#                 metadata["country"] = val
#             if att in metadata:
#                 if att == 'isolation_source':
#                     found = False
#                     for cat, keywords in ontology:
#                         if any([x in val.lower() for x in keywords]):
#                             found = True
#                             metadata[att] = cat
#                             break
#                     if not found:
#                         _logger.warning("Source not identified: " + val)
#                     metadata['source_note'] = val
#                     # if stat[1] not in isolation_source:
#                     #     metadata[stat[0].strip()] = 'other'
#                     #     metadata['source_note'] = stat[1]
#                 elif att == 'BioSample':
#                     metadata['notes'] = metadata[
#                         'notes'] + ' BioSample=' + val + ', '
#                 # elif stat[0].strip() == 'run':
#                 #     metadata['notes'] = metadata['notes'] + ' run='
#                                           + stat[1]
#                 #     + ', '
#                 else:
#                     metadata[stat[0].strip()] = stat[1]
#         metadata['file_names'] = '%s_1.fastq.gz %s_2.fastq.gz' % (
#             accession.strip('\n'), accession.strip('\n'))
#         # metadata['file_names'] = '%s.fastq' % (accession.strip('\n'))
#         metadata['notes'] = metadata['notes'] + ' run=' + accession + ', '
#         metadata['sample_name'] = metadata['strain']
#     return metadata


# def get_metadata_from_EBI(accession, attrs):
#
#     metadata = {
#         "sample_name": accession,
#         "group_name": "",
#         "file_names": "",
#         "sequencing_platform": "Illumina",
#         "sequencing_type": "paired",
#         "pre_assembled": "no",
#         "sample_type": "isolate",
#         "organism": bioproject_organism[bioID],
#         "strain": "",
#         "subtype": "",
#         "country": "",
#         "region": "",
#         "city": "",
#         "zip_code": "",
#         "longitude": "",
#         "latitude": "",
#         "location_note": "",
#         "isolation_source": "other",
#         "source_note": "",
#         "pathogenic": "unknown",
#         "pathogenicity_note": "",
#         "collection_date": "",
#         "collected_by": "",
#         "usage_restrictions": "private",
#         "release_date": "",
#         "email_address": "",
#         "notes": "",
#         "upload_dir": 1,
#         "batch": "true"
#     }
#     isolation_source = [
#         "human", "water", "food", "animal", "laboratory", "other"]
#     url = 'http://www.ncbi.nlm.nih.gov/sra/?term=' + accession
#           + '&format=text'
#     data = urllib.urlopen(url).read()
#     match = re.findall(r"Sample Attributes: (.+)\n", data)
#     _logger.info(m)
#     for answer in match:
#         for attributes in answer.split(';'):
#             stat = attributes.split('=')
#             _logger.info(stat)
#             if stat[0].strip() == 'geo_loc_name' and ":" in stat[1]:
#                 metadata["country"] = stat[1].split(":")[0]
#                 metadata["region"] = stat[1].split(":")[1]
#             elif stat[0].strip() == 'geo_loc_name':
#                 metadata["country"] = stat[1]
#             if stat[0].strip() in metadata:
#                 if stat[0].strip() == 'isolation_source':
#                     if stat[1] not in isolation_source:
#                         metadata[stat[0].strip()] = 'other'
#                         metadata['source_note'] = stat[1]
#                 elif stat[0].strip() == 'BioSample':
#                     metadata['notes'] = metadata[
#                         'notes'] + ' BioSample=' + stat[1] + ', '
#                 # elif stat[0].strip() == 'run':
#                 #     metadata['notes'] = metadata['notes'] + ' run='
#                       + stat[1]
#                 #     + ', '
#                 else:
#                     metadata[stat[0].strip()] = stat[1]
#         metadata['file_names'] = '%s_1.fastq.gz %s_2.fastq.gz' % (
#             accession.strip('\n'), accession.strip('\n'))
#         # metadata['file_names'] = '%s.fastq' % (accession.strip('\n'))
#         metadata['notes'] = metadata['notes'] + ' run=' + accession + ', '
#         metadata['sample_name'] = metadata['strain']
#     return metadata


def get_fastq_from_list(bioproject, dir):
    """
    Get Fastq from list of Ids

    :param bioproject: Bioproject from SRA
    :param dir: Output folder
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

        if line / total < 0.5 and total > 19:
            FOLDER = dir + '_batch_1/' + str(line) + '/'
        elif line / total >= 0.5 and total > 19:
            FOLDER = dir + '_batch_2/' + str(line) + '/'
        else:
            FOLDER = dir + '/' + str(line) + '/'
        dbio = Path(FOLDER)
        dbio.makedirs_p()
        if not os.path.exists(dir + '/' + accession + '.fastq'):
            _logger.info(accession.strip() + ' new')
            _logger.info("%s" % (FOLDER))
            os.system("fastq-dump %s --split-3 --bzip2 --outdir %s"
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
    total = len([aux for aux in f])
    _logger.error(total)
    f = open(bioproject_files[bioproject], 'r')
    for accession in f:
        accession = accession.strip()
        _logger.info(accession)
        metadata = get_metadata(accession, bioproject)
        _logger.info(metadata)

        if line / total < 0.5 and total > 19:
            FOLDER = dir + '_batch_1/' + str(line) + '/'
        elif line / total >= 0.5 and total > 19:
            FOLDER = dir + '_batch_2/' + str(line) + '/'
        else:
            FOLDER = dir + '/' + str(line) + '/'

        dbio = Path(FOLDER)
        dbio.makedirs_p()
        f = open(FOLDER + 'meta.json', 'w')
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
    url = 'http://www.ebi.ac.uk/ena/data/warehouse/filereport?accession=' + \
        accession + '&result=read_run'
    data = urllib.urlopen(url).read()
    try:
        table = pd.read_csv(StringIO(data), sep='\t')
        if table.index != []:
            if isinstance(table['run_accession'][0], type('')):
                for accession in table['run_accession']:
                    try:
                        retcode = call(
                            "fastq-dump %s --split-3 --bzip2 --outdir %s" %
                            (accession, dir))
                        if retcode < 0:
                            _logger.error("Child was terminated by signal")
                        else:
                            _logger.error("Child returned")
                    except OSError as e:
                        return accession
            else:
                _logger.warning(table['run_accession'][0])
                _logger.warning(type(table['run_accession'][0]))
                return accession
        else:
            return accession
    except Exception as e:
        _logger.error("Download accession data failed %s" % accession)
        _logger.error(url)
        _logger.error(data)


def download_fastqSRA(accession, dir):
    """
    Download Fastq associated with Accession from ENA

    :param run_accession: Run Accession ID from ENA
    :return: True
    """

    url = 'http://www.ncbi.nlm.nih.gov/sra/?term=' + accession + '&format=text'
    _logger.info(url)
    data = urllib.urlopen(url).read()
    # print(data)
    m = re.findall(r"Run #1: (\w+), ", data)
    for run in m:
        _logger.error(run)
        os.system("fastq-dump %s --split-3 --bzip2 --outdir %s" % (run, dir))


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
        # if type(table['fastq_ftp'][0]) == type('str'):
        if isinstance(table['fastq_ftp'][0], type('')):
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
                _logger.info(e[0])
        else:
            _logger.info("All accessions downloaded succesfully!")


def download_taxonomy():
    """
    Example input data

    :param args: -t TAXID ORGANISM
    :return:
    """

    # logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    args = parse_args_taxonomy(sys.argv[1:])
    if args.t is not None:
        download_species(
            [{"name": args.t[0], "tax_id": args.t[1]}],
            args.output[0]
        )
    else:
        _logger.error('Usage: [-t TAXID ORGANISM]')

def download_accession_list():
    # logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    args = parse_args_accessions(sys.argv[1:])
    if args.a is not None:
        _logger.info('Good!')
    else:
        _logger.error('Usage: [-a BIOPROJECTID ORGANISM PATH]')


def main(args):
    """
    Example input data

    :param species: {"name": SPECIES_NAME, "tax_id": ENA_TAX_ID}
    :return:
    """
    args = parse_args(args)
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
        d = Path('./data_split/bioprojects/%s' % species_path)
        d.makedirs_p()
        for id in project["id"]:
            _logger.info(id)
            dir = './data_split/bioprojects/%s/PRJNA%s' % (species_path, id)
            # dbio = Path(dir)
            # dbio.makedirs_p()
            # get_fastq_url_from_bioproject(id, dir)
            # get_metadata_from_list(id, dir)
            get_fastq_from_list(id, dir)

    species = [{"name": 'Lysteria', "tax_id": 1639},
               {"name": 'Salmonella', "tax_id": 590}]
    # download_species(species)
    _logger.info("Script ends here")


def run():
    # logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main(sys.argv[1:])


if __name__ == "__main__":
    download_taxonomy(sys.argv[1:])
