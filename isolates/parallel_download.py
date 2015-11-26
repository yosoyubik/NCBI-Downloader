#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' Parallel NCBI download script '''
import sys, os, argparse
from subprocess import Popen, PIPE
from pipes import quote
from download_accession_list import acctypes
from isolates.metadata import ExtractExperimentIDs

def parse_args(args):
    """
    Parse command line parameters

    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser(
        description="Download script of isolates from" +
                    "ENA taxonomy or Accession list")
    parser.add_argument(
        '-a',
        metavar=('PATH'),
        help='Format: [PATH]\n' +
             'to file containing list of ACCESSION IDs, 1 per line\n' +
             'Name of the file is used to identify the isolates downloaded.'
    )
    parser.add_argument(
        '-m',
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
        '--all_runs_as_samples',
        action="store_true",
        dest="all_runs_as_samples",
        default=False,
        help=('Treat all runs associated to a sample as separate samples. '
              'Default is to combine them into one run.\n')
    )
    parser.add_argument(
        '-n',
        '--nodes',
        dest="nodes",
        default=1,
        help=('Number of parallel batch jobs requested [default: 1]\n')
    )
    parser.add_argument(
        '-out',
        metavar=('OUTPUT'),
        required=True,
        help='Path to save isolates'
    )
    return parser.parse_args(args)

def SetupParallelDownload(accession_list):
    """ Expand list of accession IDs to experiment or lower, and devide into
    parallel batch jobs
    """
    experiments = []
    failed_accession = []
    with open(accession_list, 'r') as f:
        for l in f:
            accession = l.strip()
            if accession == '': continue
            # Determine accession type
            if accession[:3] in acctypes:
                accession_type = acctypes[accession[:3]]
            else:
                print("unknown accession type for '%s'!"%accession)
                failed_accession.append(accession)
                continue
            print("Acc Found: %s (%s)", accession, accession_type)
            if accession_type in ['study', 'sample']:
                experiments.extend(ExtractExperimentIDs(accession))
            elif accession_type in ['experiment', 'run']:
                experiments.append(accession)
    if failed_accession:
        print("The following accessions were not downloaded!")
        print('\n'.join(failed_accession))
    else:
        print("All accessions downloaded succesfully!")
    return experiments

def GetCMD(prog, args):
    cmd = [prog]
    cmd.extend([str(x) if not isinstance(x, (unicode)) else x.encode('utf-8')
                for x in [quote(x) for x in self.args]])
    return ' '.join(cmd)

ceil = lambda a: int(a) + (a%1>0)

def main():
    args = parse_args(sys.argv[1:])
    if args.a is not None:
        experiments = SetupParallelDownload(args.a)
        elen = len(experiments)
        if elen > 0:
            # Create out directory
            cwd = os.getcwd()
            out_dir = "%s/%s/"%(cwd, args.out)
            if not os.path.exists(out_dir): os.mkdir(out_dir)
            # Split experiments in batches
            epb = ceil(elen / float(args.nodes))
            batches = [experiments[s:s+epb] for s in xrange(0,elen,epb)]
            # Run batch downloads
            ps = []
            for batch_dir, eids in enumerate(batches):
                # Save experiment IDs to file
                batch_acc_list = "%s/%s.acc.txt"%(out_dir, batch_dir)
                with open(batch_acc_list, 'w') as f: f.write('\n'.join(eids))
                # Prepare cmdline
                nargs =['-a', batch_acc_list,
                        '-m', args.m,
                        '-out', "%s/%s/"%(out_dir, batch_dir)
                        ]
                if args.preserve: nargs.append('-p')
                if args.all_runs_as_samples: nargs.append('--all_runs_as_samples')
                cmd = GetCMD("download-accession-list", nargs)
                # Execute batch download
                ps.append(Popen(cmd, shell=True, executable="/bin/bash"))
            # Wait for all batches to finish
            esum = 0
            for p in ps:
                esum += p.wait()
            if esum == 0:
                print('All batches finished succesfully!')
            else:
                print('Something failed!')
        else:
            print('No experiments could be found!')
    else:
        print('Usage: -a PATH -o ORGANISM -out PATH [-m JSON]')

if __name__ == "__main__":
    main()