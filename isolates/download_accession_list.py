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
from shutil import rmtree, move
from tempfile import mkdtemp

from subprocess import call
from progressbar import Bar, Percentage, ProgressBar, ETA

from isolates.metadata import metadata_obj
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

# CLASSES
class TemporaryDirectory(object):
   """Create and return a temporary directory.  This has the same
   behavior as mkdtemp but can be used as a context manager.  For
   example:
   
   >>> import os
   >>> tmpfile = 'file.ext'
   >>> with TemporaryDirectory() as tmpdir:
   ...    print "Was tmpdir created? %s"%os.path.exists(tmpdir)
   ...    os.chdir(tmpdir)
   ...    with open(tmpfile, 'w') as f:
   ...       f.write('Hello World!')
   ...    print "Was tmpfile created? %s"%os.path.exists(tmpfile)
   Was tmpdir created? True
   Was tmpfile created? True
   >>> print "Does tmpfile still exist? %s"%os.path.exists(tmpfile)
   Does tmpfile still exist? False
   >>> print "Does tmpdir still exist? %s"%os.path.exists(tmpdir)
   Does tmpdir still exist? False
   
   Upon exiting the context, the directory and everything contained
   in it are removed.
   This method is not implemented in python-2.7!
   """
   def __init__(self, suffix="", prefix="tmp", dir=None):
      self.name = None
      self.name = mkdtemp(suffix, prefix, dir)
   def __enter__(self):
      return self.name
   def cleanup(self, _warn=False):
      if self.name:
         try: rmtree(self.name)
         except: print('Could not remove %s'%self.name)
         else: self.name = None
   def __exit__(self, exc, value, tb):
       self.cleanup()

def flipdict(d):
    ''' switch keys and values, so that all values are keys in a new dict '''
    return dict(zip(*list(reversed(zip(*[(k, v) for k in d for v in d[k]])))))


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
    parser.add_argument(
        '-out',
        nargs=1,
        metavar=('OUTPUT'),
        required=True,
        help='Path to save isolates'
    )
    return parser.parse_args(args)

def ExtractSampleMetadata(accession, json=None):
    # Identify BIOSAMPLE ID
    # Extract sample metadata
    m = metadata_obj(accession, json)
    return m

def DownloadRunFiles(m, tmpdir, _logger):
    # Download run files
    try:
        s = Sequence(m.accessions['query'], tmpdir)
        s.download_fastq()
        if not s.error:
            _logger.info("Downloaded files: %s", ','.join(s.files))
            return s.files
        else: return None
    except ValueError, e:
        _logger.error(e)
        return None

def CreateSampleDir(sfiles, m, sample_dir, preserve=False):
    sample_dir = str(sample_dir)
    if len(sfiles) == 0:
        _logger.error("Error: No files were found! (%s)"%sample_dir)
        return False
    if not os.path.exists(sample_dir):
        _logger.info("Create sample dir: %s", sample_dir)
        # Create 'sample' dir
        os.mkdir(sample_dir)
        # Move files from tmpdir to sample dir
        for sf in sfiles: move(sf, sample_dir)
    elif not preserve:
        # Empty sample directory
        for fn in os.listdir(sample_dir):
            os.unlink("%s/%s"%(sample_dir, fn))
        # Move files from tmpdir to sample dir
        for sf in sfiles: move(sf, sample_dir)
    # Update and create metadata file
    try:
        m.metadata["file_names"] = ' '.join(
            [os.path.basename(sf).replace(' ','_')
                for sf in sfiles
                if not os.path.basename(sf) == 'meta.json']
            )
        m.save_metadata(sample_dir)
    except ValueError, e:
        _logger.error(e)
        return False
    else:
        return True

def download_fastq_from_list(accession_list, output, json, preserve=False):
    """
    Get Fastq from list of IDs

    :param accession_list: List of accessions
    :param dir: Output folder
    """
    acctypes = flipdict({ # flipdict reverses the dictionary!
        'study':        ['PRJ', 'SRP', 'ERP'],
        'sample':       ['SAM', 'SRS', 'ERS'],
        'experiment':   ['SRX', 'ERX'],
        'run':          ['SRR', 'ERR']
    })
    metadata = []
    cwd = os.getcwd()
    with open(accession_list, 'r') as f:
        # Setup batch dir
        batch_dir = "%s/%s/"%(cwd, output)
        if not os.path.exists(batch_dir): os.mkdir(batch_dir)
        os.chdir(batch_dir)
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
        failed_accession = []
        for i, l in enumerate(f):
            accession = l.strip()
            if accession == '': continue
            # Determine accession type
            if accession[:3] in acctypes:
                accession_type = acctypes[accession[:3]]
            else:
                _logger.error("unknown accession type for '%s'!"%accession)
                failed_accession.append(accession)
                continue
            _logger.info("Acc Found: %s (%s)", accession, accession_type)
            if accession_type == 'study':
                # ToDo
                # Find all associated samples
                # Loop over all study samples
                #   extract_sample_metadata()
                #   Find all experiments for the given sample
                #   Loop experiments
                #     Find all runs associated to the experiment
                #     download_run_files()
                #     if option --all_runs_as_samples
                #       loop runs
                #         create_sample_dir()
                #     else:
                #       combine_runs_to_run()
                #       create_sample_dir()
                _logger.error("study accession are not supported yet! (%s)"%accession)
                failed_accession.append(accession)
                continue
            elif accession_type == 'sample':
                # ToDo
                # extract_sample_metadata()
                # Find all experiments for the given sample
                # Loop experiments
                #   Find all runs associated to the experiment
                #   download_run_files()
                #   if option --all_runs_as_samples
                #     loop runs
                #       create_sample_dir()
                #   else:
                #     combine_runs_to_run()
                #     create_sample_dir()
                _logger.error("sample accession are not supported yet! (%s)"%accession)
                failed_accession.append(accession)
                continue
            elif accession_type == 'experiment':
                # ToDo
                # extract_sample_metadata()
                # Find all runs associated to the experiment
                # download_run_files()
                # if option --all_runs_as_samples
                #   loop runs
                #     create_sample_dir()
                # else:
                #   combine_runs_to_run()
                #   create_sample_dir()
                _logger.error("experiment accession are not supported yet! (%s)"%accession)
                failed_accession.append(accession)
                continue
            elif accession_type == 'run':
                m = ExtractSampleMetadata(accession, json)
                if m.valid_metadata():
                    with TemporaryDirectory() as tmpdir:
                        os.chdir(batch_dir)
                        sample_dir = "%s/%s/"%(batch_dir, i)
                        sfiles = [x for x in os.listdir(sample_dir) if any([y in x for y in ['fq','fastq']])]
                        if not preserve or len(sfiles) == 0:
                            sfiles = DownloadRunFiles(m, tmpdir, _logger)
                        if sfiles is not None:
                            success = CreateSampleDir(sfiles, m, sample_dir, preserve)
                            if not success:
                                failed_accession.append(accession)
                                continue
                        else:
                            _logger.error("Files could not be retrieved! (%s)"%accession)
                            failed_accession.append(accession)
                            continue
                else:
                    _logger.error("Metadata Invalid! (%s)"%accession)
                    failed_accession.append(accession)
                    continue
            pbar.update(i)
        pbar.finish()
        if failed_accession:
            _logger.info("The following accessions were not downloaded!")
            _logger.info('\n'.join(failed_accession))
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
