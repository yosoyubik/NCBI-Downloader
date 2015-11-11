#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

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
            self.metadata['sample_name'] = accession.strip()
        self.url = 'http://www.ncbi.nlm.nih.gov/sra/?term=%s&format=text' % (
            accession.strip())
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
        self.metadata['files_names'] = files

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
                finally:
                    location_hash[val] = geo_dict
        self.metadata.update(geo_dict)

    def update_attributes(self):
        '''
        XXX
        :return: accessionid of non identified sources
        '''
        # FIXME: Major problem:
        #   sequencing platform cannot be unknown, when pre_assembled is no.
        #   The correct answer here is Illumina.
        #   collection date should follow our format: 1998-05-29
        # Minor issues:
        #   City should be Melbourrne
        #   Region should be empty or Victoria
        #   Organism should only be the genus species annotation, anything else
        #   should be left out  (Enterococcus faecium)
        #   notes contain a lot of unnecessary spaces, and it does not contain
        #   the SRR identifier nor the biosample ID as would be preferred, and
        #   necessary for later annotation of the MLST to the data.
        match = re.findall(r'Run #1: (.+)\n', self.data)
        for answer in match:
            self.accession = answer.split(',')[0]

        match = re.findall(r'Sample Attributes: (.+)\n', self.data)
        for answer in match:
            for attributes in answer.split(';'):
                stat = attributes.split('=')
                att = stat[0].strip('/ ').lower().replace('\'', '')
                val = stat[1].strip('\' ').replace('\'', '\`')
                if att == 'geo_loc_name' and ':' in stat[1]:
                    self.__interpret_loc(val)
                    # self.metadata['country'] = val.split(':')[0]
                    # self.metadata['city'] = val.split(':')[1]
                elif att == 'geo_loc_name':
                    self.__interpret_loc(val)
                    # self.metadata['country'] = val
                elif att == 'serovar':
                    self.metadata['subtype']['serovar'] = val
                elif att == 'mlst':
                    self.metadata['subtype']['mlst'] = val
                elif att == 'isolation_source':
                    found = False
                    for cat, keywords in ontology:
                        if any([x in val.lower() for x in keywords]):
                            found = True
                            self.metadata[att] = cat
                            break
                    if not found:
                        _logger.warning(
                            'Source not identified: %s, %s',
                            val, self.accession
                        )
                    self.metadata['source_note'] = val
                elif att == 'BioSample':
                    self.metadata['biosample'] = val
                elif att == 'collection_date':
                    self.metadata[att] = self.__format_date(
                        *self.__interpret_date(val)
                    )
                    if self.metadata[att] == '':
                        _logger.warning(
                            'Date Empty: %s',
                            val, self.accession
                        )
                elif att == 'geographic location':
                    self.__interpret_loc(val)
                elif att in self.metadata:
                    self.metadata[att] = val
                else:
                    self.metadata['notes'] = '%s %s: %s,' % (
                        self.metadata['notes'], att, val)

        match1 = re.findall(r'Sample Attributes: (.+)\n', self.data)
        match2 = re.findall(r'Platform Name: (.+)\n', self.data)
        if match1:
            for answer in match1:
                self.metadata['sequencing_platform'] = platforms.get(
                    answer.lower(), 'unknown'
                )
        elif match2:
            for answer in match2:
                self.metadata['sequencing_platform'] = platforms.get(
                    answer.lower(), 'unknown'
                )
        else:
            self.metadata['sequencing_platform'] = 'unknown'

        match = re.findall(r'Library Layout: (.+)\n', self.data)
        for answer in match:
            self.metadata['sequencing_type'] = answer.split(',')[0].lower()

        match = re.findall(r'Sample Accession: (.+)\n', self.data)
        for answer in match:
            self.sample_accession = answer


class MetadataBioSample(Metadata):
    def __init__(self, accession, json=default):
        super(MetadataBioSample, self).__init__(accession, json)
        # ncbi = 'http://www.ncbi.nlm.nih.gov/biosample/'
        # self.url = '%s?term=%s&report=full&format=text' % (
        #     ncbi, accession.strip())
        # self.data = urllib.urlopen(self.url).read()
        # self.organism = copy.deepcopy(metadata)

    def update_biosample_attributes(self):
        ncbi = 'http://www.ncbi.nlm.nih.gov/biosample/'
        url = '%s?term=%s&report=full&format=text' % (
            ncbi, self.sample_accession)
        data = urllib.urlopen(url).read()

        match = re.findall(r'Organism: (.+)\n', data)
        if match != []:
            self.metadata['organism'] = match[0]
        else:
            self.metadata['organism'] = ''

        match = re.findall(r'Sample name: (.+)', data)
        if match == []:
            self.metadata['sample_name'] = self.accession.strip()
        else:
            self.metadata['sample_name'] = match[0].split(';')[0]

        # match = re.findall(r'SRA: (.+)', data)
        # if match == []:
        #     self.accession = self.accession.strip()
        # else:
        #     self.accession = match[0].split(';')[0]
