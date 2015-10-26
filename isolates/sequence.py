#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

'''

from source import ontology, platforms, location_hash
from template import metadata, mandatory_fields
import re
import urllib
import copy
import logging
import sys
from path import Path

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
    _errors = {}
    _sequence_id = 0

    def __init__(self, accession, dir):
        self.accession = accession
        self.url = 'http://www.ebi.ac.uk/ena/data/warehouse/filereport?accession=%s&result=read_run' % accession
        self.data = urllib.urlopen(self.url).read()
        self.dir = '%s/%s/' % (dir, str(self._sequence_id))
        self.files = []
        self.data = urllib.urlopen(self.url).read()
        self.download = 'fastq-dump %s --split-3 --bzip2 --outdir %s' % (
                         accession, dir)

    @property
    def errors(self):
        """ Get errors for all sequences """
        return self._errors

    @property
    def id(self):
        return self._sequence_id

    def download_fastq(self):
        '''
        Download Fastq associated with Accession from ENA

        :param run_accession: Run Accession ID from ENA
        :return: True
        '''
        try:
            table = pd.read_csv(StringIO(self.data), sep='\t')
        except Exception as e:
            _logger.error('Download accession data failed %s', self.accession)
            _logger.error('URL: %s', self.url)
            self._errors[self.accession] = 'Download accession data failed'
        else:
            if table.index != []:
                if isinstance(table['run_accession'][0], type('')):
                    for accession in table['run_accession']:
                        try:
                            Path(self.dir).makedirs_p()
                            retcode = call(self.download)
                            if retcode < 0:
                                _logger.error('Child was terminated by signal')
                                self._errors[self.accession] = 'Child was'\
                                                               'terminated'\
                                                               '(signal)'
                            else:
                                _logger.info('Success: %s', self.accession)
                                self.files = [
                                    f.abspath() for f in Path(self.dir).files
                                ]
                                self._sequence_id += 1
                        except OSError as e:
                            _logger.error('FastQ Failed: %s', self.accession)
                            self._errors[self.accession] = 'FastQ Failed'
                else:
                    _logger.error('Empty \'run accession\': %s', self.accession)
                    self._errors[self.accession] = 'Empty \'run accession\''
            else:
                _logger.error('Empty table: %s', self.accession)
                self._errors[self.accession] = 'Empty table'
