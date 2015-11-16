#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
hep hey
'''
import re
import urllib
import copy
import logging
import sys
import json
import io
import geocoder
from datetime import datetime
from source import ontology, platforms, location_hash
from template import metadata, default

# Setup of what?
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='%(levelname)s:%(message)s',
    filename='metadata.log',
    filemode='w'
)
_logger = logging.getLogger(__name__)


class Metadata(object):
    '''  '''
    def __init__(self, accession, json=default):
        self.metadata = copy.deepcopy(metadata)
        self.metadata.update(json["seed"])
        if self.metadata['sample_name'] == 'ACCESSION':
            self.metadata['sample_name'] = accession
        self.url = 'http://www.ncbi.nlm.nih.gov/sra/?term=%s&format=text' % (
            accession)
        self.data = urllib.urlopen(self.url).read()
        self.mandatory = json['mandatory']
        self.sample_accession = ''
        self.accession = ''

    def valid_metadata(self):
        '''
        Checks if metadata is valid
        :return: True if all mandatory fields are not ''
        '''
        for i in self.mandatory:
            if self.metadata[i] == '':
                return False
                break
        return True

    def save_metadata(self, dir):
        '''
        Writes self.metadata as meta.json in dir
        :param: dir
        :return: True
        '''
        f = open('%s/meta.json' % dir, 'w')
        f.write(json.dumps(self.metadata, ensure_ascii=False))
        f.close()
        return True

    def update_files(self, files):
        '''
        Checks if metadata is valid
        :return: True if all mandatory fields are not ''
        '''
        self.metadata['file_names'] = files

    def __format_date(self, yyyy=None, mm=None, dd=None):
        '''
        This method stringify the date tuple using a standard format:
          YYYY-MM-DD or
          YYYY-MM or
          YYYY
        If all arguments are None, FormatDate returns an empty string
        '''
        date = ''
        if yyyy is not None and yyyy != '':
            if mm is not None and mm != '':
                if dd is not None and dd != '':
                    date = '%04d-%02d-%02d' % (yyyy, mm, dd)
                else:
                    date = '%04d-%02d' % (yyyy, mm)
            else:
                date = '%04d' % (yyyy)
        return date

    def __interpret_date(self, val):
        '''
        This function will try to interpret the
        :param: val Date
        :return: Tuple of integers: (yyyy, mm, dd) or (None, None, None) if
            value not identified
            >>> InterpretDate('Feb-30-2014')
            (2014, 2, 30)
            >>> InterpretDate('Feb-2014')
            ('2014', 2, None)
        '''
        month = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
        yyyy, mm, dd = None, None, None
        if '/' in val:
            # American style
            try:
                mm, dd, yyyy = val.split('/')
            except:
                pass
        elif '-' in val:
            # European style
            tmp = val.split('-')
            lens = [len(x) for x in tmp]
            lenl = len(lens)
            if lenl == 3:
                if lens[2] == 4:
                    yyyy = tmp[2]
                    if tmp[1] in month and lens[0] <= 2:
                        mm = month.index(tmp[1]) + 1
                        dd = tmp[0]
                    elif tmp[0] in month and lens[1] <= 2:
                        mm = month.index(tmp[0]) + 1
                        dd = tmp[1]
                    elif lens[0] <= 2 and lens[1] <= 2:
                        mm = tmp[1]
                        dd = tmp[0]
                elif lens[0] == 4:
                    yyyy = tmp[0]
                    if tmp[1] in month and lens[2] <= 2:
                        mm = month.index(tmp[1]) + 1
                        dd = tmp[2]
                    elif lens[1] <= 2 and lens[2] <= 2:
                        mm = tmp[1]
                        dd = tmp[2]
                elif lens[0] <= 2 and lens[2] == 2 and tmp[1] in month:
                    yearnow = datetime.now().year
                    yyyy = int(str(yearnow)[:-2] + tmp[2])
                    if yyyy > yearnow:
                        yyyy = int(str(yearnow-100)[:-2] + tmp[2])
                    mm = month.index(tmp[1]) + 1
                    dd = tmp[0]
            elif lenl == 2:
                if lens[0] == 4:
                    yyyy = tmp[0]
                    if tmp[1] in month:
                        mm = month.index(tmp[1]) + 1
                    elif lens[1] <= 2:
                        mm = tmp[1]
                if lens[1] == 4:
                    yyyy = tmp[1]
                    if tmp[0] in month:
                        mm = month.index(tmp[0]) + 1
                    elif lens[0] <= 2:
                        mm = tmp[0]
                elif lens[1] == 2 and tmp[0] in month:
                    yyyy, mm = '20' + tmp[1], month.index(tmp[0]) + 1
                elif lens[0] == 2 and tmp[1] in month:
                    yyyy, mm = '20' + tmp[0], month.index(tmp[1]) + 1
        elif len(val) == 4:
            yyyy = val
        return (int(yyyy) if yyyy is not None else None,
                int(mm) if mm is not None else None,
                int(dd) if dd is not None else None)

    def __interpret_loc(self, val):
        '''  '''
        geo_dict = {
            'country': '',
            'region': '',
            'city': '',
            'zip_code': '',
            'longitude': '',
            'latitude': '',
            'location_note': ''
        }
        type_map = {
            'country': 'country',
            'postal_code': 'zip_code',
            'administrative_area_level_1': 'region',
            'locality': 'city'
        }
        val = val.lower()
        if val not in location_hash.keys():
            try:
                g = geocoder.google(val)
            except Exception, e:
                _logger.warning(
                    'Geocoder error %s', self.accession
                )
                location_hash[val] = ('', '', '', '', val)
            else:
                geo_dict['longitude'] = g.lng
                geo_dict['latitude'] = g.lat
                geo_dict['location_note'] = g.location
                try:
                    results = g.content['results'][0]
                    for x in results['address_components']:
                        for a_type in x['types']:
                            if a_type in type_map:
                                m_type = type_map[a_type]
                                geo_dict[m_type] = x['long_name']
                                break
                except:
                    try:
                        a_tmp = g.address.split(',')
                        if len(address_tmp) > 2:
                            geo_dict['city'] = a_tmp[0]
                            geo_dict['region'] = a_tmp[-2]
                            geo_dict['country'] = a_tmp[-1]
                        elif len(address_tmp) == 2:
                            geo_dict['city'] = a_tmp[0]
                            geo_dict['country'] = a_tmp[-1]
                        elif len(address_tmp) == 1:
                            geo_dict['country'] = a_tmp[0]
                    except:
                        pass
                    else:
                        try:
                            geo_dict['zip_code'] = int(
                                geo_dict['city'].split(' ')[0]
                            )
                        except:
                            pass
                location_hash[val] = geo_dict
        else:
            geo_dict = location_hash[val]
        self.metadata.update(geo_dict)

    def update_attributes(self):
        '''
        :return: accessionid of non identified sources
        '''
        match = re.findall(r'Run #1: (.+)\n', self.data)
        if match:
            self.accession = match[0].split(',')[0].strip()

        match = re.findall(r'Sample Attributes: (.+)\n', self.data)
        lcs = {} # location parts
        for answer in match:
            for attributes in answer.split(';'):
                stat = attributes.split('=')
                att = stat[0].strip('/ ').lower().replace('\'', '')
                val = stat[1].strip('\' ').replace('\'', '\`')
                if att in ['geo_loc_name', 'geographic location']:
                    self.__interpret_loc(val)
                elif att == 'serovar':
                    self.metadata['subtype']['serovar'] = val
                elif att == 'mlst':
                    self.metadata['subtype']['mlst'] = val
                elif att in ['scientific_name', 'scientific name']:
                    self.metadata['organism'] = val
                elif att == 'strain':
                    self.metadata['strain'] = val
                elif att in ['isolation_source', 'isolation source']:
                    found = False
                    for cat, keywords in ontology:
                        if any([x in val.lower() for x in keywords]):
                            found = True
                            self.metadata['isolation_source'] = cat
                            break
                    if not found:
                        _logger.warning(
                            'Source not identified: %s, %s',
                            val, self.accession
                        )
                    self.metadata['source_note'] = val
                elif att == 'BioSample':
                    self.metadata['biosample'] = val
                elif att in ['collection_date', 'collection date']:
                    self.metadata['collection_date'] = self.__format_date(
                        *self.__interpret_date(val)
                    )
                    if self.metadata['collection_date'] == '':
                        _logger.warning(
                            'Date Empty: %s',
                            val, self.accession
                        )
                elif att in ['collected_by', 'collected by']:
                    self.metadata['collected_by'] = val
                elif att in ['country', 'region', 'city', 'zip_code']:
                    lcs[att] = val
                else:
                    self.metadata['notes'] = '%s %s: %s,' % (
                        self.metadata['notes'], att, val)
            if lcs != {}:
                h = ['country', 'region', 'city', 'zip_code']
                self.__interpret_loc( ','.join([lcs[x] for x in h if x in lcs]))
        match = re.findall(r'Platform Name: (.+)\n', self.data)
        if match:
            self.metadata['sequencing_platform'] = platforms.get(
                match[0].lower(), 'unknown'
            )
        else:
            self.metadata['sequencing_platform'] = 'unknown'

        match = re.findall(r'Library Layout: (.+)\n', self.data)
        if match:
            self.metadata['sequencing_type'] = match[0].split(',')[0].lower()

        match = re.findall(r'Sample Accession: (.+)\n', self.data)
        if match:
            self.sample_accession = match[0]
            # Extract the BioSample ID using the SRA sample ID
            if (not 'biosample' in self.metadata or
                self.metadata['biosample'] == ''):
                url = ('http://www.ncbi.nlm.nih.gov/biosample/?'
                       'term=%s&format=text')%(self.sample_accession)
                data = urllib.urlopen(url).read()
                match2 = re.findall(r'Identifiers: (.+)\n', data)
                if match2:
                    for ent in match2[0].split(';'):
                        tmp = ent.split(':')
                        if tmp[0].strip().lower() == 'biosample':
                            self.metadata['biosample'] = tmp[1].strip()
                            break


class MetadataBioSample(Metadata):
    def __init__(self, accession, json=default):
        super(MetadataBioSample, self).__init__(accession, json)
    def update_biosample_attributes(self):
        ''' Extract and set BioSample ID, Organism and Sample Name '''
        # Set NCBI url
        ncbi = 'http://www.ncbi.nlm.nih.gov'
        # Extract the SRA experiment ID and project ID using the SRA run ID
        match1 = re.findall(r'Accession: (.+)', self.data)
        match2 = re.findall(r'Study accession: (.+)', self.data)
        if match1 and match2:
            experiment_id = match1[0]
            project_id = match2[0]
            # Extract the SRA sample ID using the SRA experiment ID
            sample_id = None
            url = '%s/sra/?term=%s&format=text'%(ncbi, project_id)
            data = urllib.urlopen(url).read()
            flag = False
            for l in data.split('\n'):
                if flag:
                    if l.strip() == '': break
                    tmp = l.split(':')
                    if tmp[0] == 'Sample':
                        sample_id = tmp[1].split('(')[-1].strip(' )')
                elif l.split(':')[-1].strip() == experiment_id:
                    flag = True
            if sample_id is not None:
                # Extract the BioSample ID using the SRA sample ID
                url = '%s/biosample/?term=%s&format=text' % (ncbi, sample_id)
                data = urllib.urlopen(url).read()
                match3 = re.findall(r'Identifiers: (.+)\n', data)
                if match3:
                    for ent in match3[0].split(';'):
                        tmp = ent.split(':')
                        if tmp[0].strip().lower() == 'biosample':
                            self.metadata['biosample'] = tmp[1].strip()
                            break
                # Extract Organism
                match4 = re.findall(r'Organism: (.+)\n', data)
                if match4:
                    self.metadata['organism'] = ' '.join(match4[0].split()[:2])
                else:
                    self.metadata['organism'] = ''
                # Sample Name
                match5 = re.findall(r'Sample name: (.+)', data)
                if (match5 and
                    match5[0].split(';')[0].lower() not in
                    ['unidentified', 'missing', 'unknown', 'na']
                    ):
                    self.metadata['sample_name'] = match5[0].split(';')[0]
                else:
                    self.metadata['sample_name'] = self.accession
