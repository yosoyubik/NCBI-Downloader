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
import json
import argparse
from shutil import move
from progressbar import Bar, Percentage, ProgressBar, ETA

from isolates import __version__, TemporaryDirectory
from isolates.log import _logger
from isolates.metadata import (ExtractExperimentMetadata,
                               ExtractExperimentIDs_acc)
from isolates.sequence import Sequence
from isolates.source import acctypes

__author__ = "Jose Luis Bellod Cisneros"
__coauthor__ = "Martin C F Thomsen"
__copyright__ = "Jose Luis Bellod Cisneros"
__license__ = "none"

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
        '-out',
        nargs=1,
        metavar=('OUTPUT'),
        required=True,
        help='Path to save isolates'
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
        '--all_runs_as_samples',
        action="store_true",
        dest="all_runs_as_samples",
        default=False,
        help=('Treat all runs associated to a sample as separate samples. '
              'Default is to combine them into one run.\n')
    )
    parser.add_argument(
        '--skip_files',
        action="store_true",
        dest="skip_files",
        default=False,
        help=('Treat all runs associated to a sample as separate samples. '
              'Default is to combine them into one run.\n')
    )
    return parser.parse_args(args)

def DownloadRunFiles(runid, tmpdir):
    # Download run files
    try:
        s = Sequence(runid, tmpdir)
        s.download_fastq()
        if not s.error:
            _logger.info("Downloaded files: %s", ','.join(s.files))
            return s.files
        else: return None
    except ValueError, e:
        _logger.error(e)
        return None

def CreateSampleDir(sfiles, m, sample_dir, preserve=False, skip_files=False):
    sample_dir = str(sample_dir)
    if not skip_files and len(sfiles) == 0:
            _logger.error("Error: No files were found! (%s)", sample_dir)
            return False
    if not os.path.exists(sample_dir):
        _logger.info("Create sample dir: %s", sample_dir)
        # Create 'sample' dir
        os.mkdir(sample_dir)
        # Move files from tmpdir to sample dir
        for sf in sfiles: move(sf, sample_dir)
    elif not preserve and not skip_files:
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

def download_fastq_from_list(accession_list, output, json, preserve=False, all_runs_as_samples=False, skip_files=False):
    """
    Get Fastq from list of IDs

    :param accession_list: List of accessions
    :param dir: Output folder
    """
    metadata = []
    cwd = os.getcwd()
    with open(accession_list, 'r') as f:
        # Setup batch dir
        batch_dir = "%s/%s/"%(cwd, output)
        if not os.path.exists(batch_dir): os.mkdir(batch_dir)
        os.chdir(batch_dir)
        # Set logging
        _logger.Set(filename="%s/download-acceession-list.log"%batch_dir)
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
        sample_dir_id = 0
        for i, l in enumerate(f):
            accession = l.strip()
            if accession == '': continue
            # Determine accession type
            if accession[:3] in acctypes:
                accession_type = acctypes[accession[:3]]
            else:
                _logger.error("unknown accession type for '%s'!", accession)
                failed_accession.append(accession)
                continue
            _logger.info("Acc Found: %s (%s)", accession, accession_type)
            if accession_type in ['study', 'sample']:
                for experiment_id in ExtractExperimentIDs_acc(accession):
                    sample_dir_id = ProcessExperiment(
                        experiment_id, json, batch_dir,sample_dir_id, preserve,
                        failed_accession, all_runs_as_samples, skip_files)
            elif accession_type == 'experiment':
                sample_dir_id = ProcessExperiment(
                    accession, json, batch_dir,sample_dir_id, preserve,
                    failed_accession, all_runs_as_samples, skip_files)
            elif accession_type == 'run':
                sample_dir_id = ProcessExperiment(
                    accession, json, batch_dir,sample_dir_id, preserve,
                    failed_accession, all_runs_as_samples, skip_files)
            pbar.update(i)
        pbar.finish()
        if failed_accession:
            _logger.info("The following accessions were not downloaded!")
            _logger.info('\n'.join(failed_accession))
        else:
            _logger.info("All accessions downloaded succesfully!")

def ProcessExperiment(experiment_id, json, batch_dir, sample_dir_id, preserve, failed_accession, all_runs_as_samples, skip_files=False):
    _logger.info("Processing %s...", experiment_id)
    if all_runs_as_samples:
        sample_dir_id = ProcessExperimentSeparate(
            experiment_id, json, batch_dir, sample_dir_id,
            preserve, failed_accession, skip_files)
    else:
        sample_dir_id = ProcessExperimentCombined(
            experiment_id, json, batch_dir, sample_dir_id,
            preserve, failed_accession, skip_files)
    return sample_dir_id

def ProcessExperimentSeparate(experiment_id, json, batch_dir, sample_dir_id, preserve, failed_accession, skip_files=False):
    m = ExtractExperimentMetadata(experiment_id, json)
    if m.valid_metadata():
        # Check if a run ID was submitted, and if so only process that
        if experiment_id in m.runIDs: m.runIDs = [experiment_id]
        # Process the runIDs as samples
        _logger.info("Found Following Runs: %s", ', '.join(m.runIDs))
        for runid in m.runIDs:
            with TemporaryDirectory() as tmpdir:
                os.chdir(batch_dir)
                sample_dir = "%s/%s/"%(batch_dir, sample_dir_id)
                if os.path.exists(sample_dir):
                    sfiles = [x for x in os.listdir(sample_dir) if any([y in x for y in ['fq','fastq']])]
                else:
                    sfiles = []
                if not preserve or not skip_files or len(sfiles) == 0:
                    sfiles = DownloadRunFiles(runid, tmpdir)
                if sfiles is not None:
                    success = CreateSampleDir(sfiles, m, sample_dir, preserve, skip_files)
                    if success:
                        sample_dir_id += 1
                    else:
                        failed_accession.append(runid)
                else:
                    _logger.error("Files could not be retrieved! (%s)", runid)
                    failed_accession.append(runid)
    else:
        _logger.error("Metadata Invalid! (%s) %s", experiment_id, m)
        failed_accession.append(experiment_id)
    return sample_dir_id

def ProcessExperimentCombined(experiment_id, json, batch_dir, sample_dir_id, preserve, failed_accession, skip_files=False):
    m = ExtractExperimentMetadata(experiment_id, json)
    if m.valid_metadata():
        # Check if a run ID was submitted, and if so only process that
        if experiment_id in m.runIDs: m.runIDs = [experiment_id]
        # Process the runs as one sample
        _logger.info("Found Following Runs: %s", ', '.join(m.runIDs))
        with TemporaryDirectory() as tmpdir:
            os.chdir(batch_dir)
            sample_dir = "%s/%s/"%(batch_dir, sample_dir_id)
            csfiles = []
            if preserve and os.path.exists(sample_dir):
                csfiles = [x for x in os.listdir(sample_dir) if any([y in x for y in ['fq','fastq']])]
            if csfiles == [] and not skip_files:
                sfiles = []
                for runid in m.runIDs:
                    sf = DownloadRunFiles(runid, tmpdir)
                    if sf is not None:
                        sfiles.append(sf)
                    else:
                        _logger.error("Run files could not be retrieved! (%s)",
                                      runid)
                _logger.info("Found Following files sets:\n%s\n",
                             '\n'.join([', '.join(sf) for sf in sfiles]))
                # Combine sfiles into one entry
                if len(sfiles) > 1:
                    for file_no, file_set in enumerate(zip(*sfiles)):
                        ext = '.'.join(file_set[0].split('/')[-1].split('.')[1:])
                        if len(sfiles[0]) > 1:
                            new_file = "%s_%s.combined.%s"%(experiment_id,file_no+1, ext)
                        else:
                            new_file = "%s.combined.%s"%(experiment_id, ext)
                        with open(new_file, 'w') as nf:
                            for fn in file_set:
                                with open(fn, 'rb') as f:
                                    nf.write(f.read())
                        if os.path.exists(new_file):
                            csfiles.append(new_file)
                        else:
                            _logger.error("Combined file creation failed! (%s: %s)",
                                          experiment_id, file_no)
                            break
                elif isinstance(sfiles[0], list):
                    csfiles = sfiles[0]
                if csfiles == []:
                    _logger.error("Files could not be combined! (%s)",
                                  experiment_id)
                    failed_accession.append(experiment_id)
            if csfiles != [] or skip_files:
                success = CreateSampleDir(csfiles, m, sample_dir, preserve, skip_files)
                if success:
                    sample_dir_id += 1
                else:
                    failed_accession.append(experiment_id)
            else:
                _logger.error("Files could not be retrieved! (%s)",
                              experiment_id)
                failed_accession.append(experiment_id)
    else:
        _logger.error("Metadata Invalid! (%s)", experiment_id)
        failed_accession.append(experiment_id)
    return sample_dir_id

def download_accession_list():
    args = parse_args_accessions(sys.argv[1:])
    if args.a is not None:
        if args.m is not None:
            try:
                default = json.load(args.m[0])
            except ValueError as e:
                print("ERROR: Json file has the wrong format!\n", e)
                exit()
        else:
            default = None
        download_fastq_from_list(args.a[0], args.out[0], default, args.preserve, args.all_runs_as_samples, args.skip_files)
    else:
        print('Usage: -a PATH -o ORGANISM -out PATH [-m JSON]')

if __name__ == "__main__":
    download_accession_list()
