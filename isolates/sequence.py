#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

'''

from source import ontology, platforms, location_hash
import re
import urllib
import copy
import logging
import sys
from path import Path
from subprocess import call, PIPE

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='%(levelname)s:%(message)s',
    filename='sequence.log',
    filemode='w'
)
_logger = logging.getLogger(__name__)


class Sequence(object):

    # Global vars for all sequences
    __errors = {}
    __sequence_id = 0

    def __init__(self, accession, dir):
        if accession == '':
            raise ValueError('Accession can not be empty')
        self.accession = accession.strip()
        self.dir = '%s/%s/' % (dir, str(Sequence.__sequence_id))
        Path(self.dir).makedirs_p()
        self.files = []
        self.error = False
        self.download = [
            'fastq-dump', self.accession, '--split-3', '--gzip',
            '--outdir', self.dir
        ]

    @property
    def errors(self):
        """ Get errors for all sequences """
        return Sequence.__errors

    @errors.setter
    def errors(self, value):
        Sequence.__errors[self.accession] = value

    @property
    def id(self):
        return Sequence.__sequence_id

    @id.setter
    def id(self, value):
        Sequence.__sequence_id += 1

    def download_fastq(self):
        '''
        Download Fastq associated with Accession from ENA

        :param run_accession: Run Accession ID from ENA
        :return: True
        '''
        try:
            Path(self.dir).makedirs_p()
            retcode = call(self.download, stdout=PIPE)
        except OSError as e:
            _logger.error('FastQ Failed: %s [%s]', self.accession, e)
            _logger.error('CMD: %s', self.download)
            Sequence.__errors[self.accession] = 'FastQ Failed'
            self.error = True
        else:
            if retcode < 0:
                _logger.error('Child was terminated by signal')
                self.error = True
                Sequence.__errors[self.accession] = 'Child was'\
                    'terminated'\
                    '(signal)'
            else:
                _logger.info('Success: %s', self.accession)
                self.files = [
                    f.abspath() for f in Path(self.dir).files()
                ]
                Sequence.__sequence_id += 1
                # self.__sequence_id += 1
