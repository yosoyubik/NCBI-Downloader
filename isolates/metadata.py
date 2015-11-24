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
import socket
from email.mime.text import MIMEText
from subprocess import Popen, PIPE

# Setup of what?
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='%(levelname)s:%(message)s',
    filename='metadata.log',
    filemode='w'
)
_logger = logging.getLogger(__name__)

class openurl(object):
    ''' urllib library wrapper, to make it easier to use.
    >>> import urllib
    >>> with openurl('http://www.ncbi.nlm.nih.gov/sra/?term=ERX006651&format=text') as u:
    ...   for l in u:
    ...      print l.strip()
    '''
    def __init__(self, url):
        self.url = url
    def __enter__(self):
        self.u = urllib.urlopen(self.url)
        return self.u 
    def __exit__(self, type=None, value=None, traceback=None):
        self.u.close()
        self.u = None
    def __iter__(self):
        yield self.readline()
    def read(self):
        return self.u.read()
    def readline(self):
        return self.u.readline()
    def readlines(self):
        return self.u.readlines()

class mail_obj():
   '''
   >>> mail = mail_obj(['to_me@domain.com'], 'from_me@domain.com')
   >>> mail.send('Hello my subject!','Hello my body!')
   '''
   def __init__(self, recepients, sender):
      self.to = recepients
      self.fr = sender
   def send(self, subject, message):
      '''  '''
      msg = MIMEText(message)
      msg["From"] = self.fr
      msg["To"] = ', '.join(self.to) if isinstance(self.to, list) else self.to
      msg["Subject"] = subject
      p = Popen(["sendmail -r %s %s"%(self.fr, ' '.join(self.to))],
                shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
      out, err = p.communicate(msg.as_string())
      p.wait()

# Setup Mail Wrapper
if 'cbs.dtu.dk' in socket.getfqdn() or 'computerome' in socket.getfqdn():
    mail = mail_obj(['mcft@cbs.dtu.dk'], 'mcft@cbs.dtu.dk') #cgehelp
else:
    mail = None

class metadata_obj(object):
    ''' This class describes metadata associated with a sample '''
    def __init__(self, accession, settings=None):
        if settings is None: settings = default
        self.metadata = settings["seed"]
        self.mandatory = settings['mandatory']
        self.accessions = {'query': accession}
        # Set metadata collection site URL
        ncbi = 'http://www.ncbi.nlm.nih.gov'
        self.sra_url = '%s/sra/?term=%s&format=text'%(ncbi, '%s')
        self.bio_url = '%s/biosample/?term=%s&format=text' %(ncbi, '%s')
        # Extract Sample Metadata
        self.ExtractData(accession)
    def __getitem__(self, key):
        return self.metadata[key]
    def __setitem__(self, key, value):
        self.metadata[key] = value
    def ExtractData(self, query):
        ''' Extract Sample Metadata '''
        with openurl(self.sra_url%(query)) as u: qdata = u.read()
        # Extract the SRA experiment ID and project ID using the SRA run ID
        match1 = re.findall(r'Accession: (.+)', qdata)
        match2 = re.findall(r'Study accession: (.+)', qdata)
        if match1 and match2:
            self.accessions['experiment'] = match1[0]
            self.accessions['study'] = match2[0]
            # Extract the SRA sample ID using the SRA experiment ID
            with openurl(self.sra_url%(self.accessions['study'])) as u:
                sdata = u.read()
            flag = False
            for l in sdata.split('\n'):
                if flag:
                    if l.strip() == '': break
                    tmp = l.split(':')
                    if tmp[0] == 'Sample':
                        self.accessions['sample'] = tmp[1].split('(')[-1].strip(' )')
                elif l.split(':')[-1].strip() == self.accessions['experiment']:
                    flag = True
            if 'sample' in self.accessions:
                # Extract the BioSample ID using the SRA sample ID
                with openurl(self.bio_url%(self.accessions['sample'])) as u:
                    bdata = u.read()
                match3 = re.findall(r'Identifiers: (.+)\n', bdata)
                if match3:
                    for ent in match3[0].split(';'):
                        tmp = ent.split(':')
                        if tmp[0].strip().lower() == 'biosample':
                            self.accessions['biosample'] = tmp[1].strip()
                            self['biosample'] = self.accessions['biosample']
                            break
                # Extract Organism
                match4 = re.findall(r'Organism: (.+)\n', bdata)
                if match4:
                    self['organism'] = ' '.join(match4[0].split()[:2])
                else:
                    self['organism'] = ''
                # Sample Name
                match5 = re.findall(r'Sample name: (.+)', bdata)
                if (match5 and
                    match5[0].split(';')[0].lower() not in
                    ['unidentified', 'missing', 'unknown', 'na']
                    ):
                    self['sample_name'] = match5[0].split(';')[0]
                else:
                    self['sample_name'] = self.accessions['query']
        # Extract sample attributes
        match = re.findall(r'Sample Attributes: (.+)\n', qdata)
        lcs = {} # location parts
        for answer in match:
            for attributes in answer.split(';'):
                stat = attributes.split('=')
                att = stat[0].strip('/ ').lower().replace('\'', '')
                val = stat[1].strip('\' ').replace('\'', '\`')
                if att in ['geo_loc_name', 'geographic location']:
                    self.__interpret_loc(val)
                elif att == 'serovar':
                    self['subtype']['serovar'] = val
                elif att == 'mlst':
                    self['subtype']['mlst'] = val
                elif att in ['scientific_name', 'scientific name']:
                    self['organism'] = val
                elif att == 'strain':
                    self['strain'] = val
                elif att in ['isolation_source', 'isolation source']:
                    found = False
                    for d in ontology:
                        cats = [d[k][0] for k in d.keys() if k in val.lower()]
                        if cats:
                            found = True
                            self['isolation_source'] = cats[0]
                            break
                    if not found:
                        _logger.warning(
                            'Source not identified: %s, %s',
                            val, query
                        )
                        # Notify Curators By Email
                        if mail is not None:
                            mail.send('New isolation source...',
                                      'Source not identified: %s, %s'%(
                                          val, query))
                    self['source_note'] = val
                elif att == 'BioSample':
                    self['biosample'] = val
                elif att in ['collection_date', 'collection date']:
                    self['collection_date'] = self.__format_date(
                        *self.__interpret_date(val)
                    )
                    if self['collection_date'] == '':
                        _logger.warning(
                            'Date Empty: %s',
                            val, query
                        )
                elif att in ['collected_by', 'collected by']:
                    self['collected_by'] = val
                elif att in ['country', 'region', 'city', 'zip_code']:
                    lcs[att] = val
                else:
                    self['notes'] = '%s %s: %s,' % (
                        self['notes'], att, val)
            if lcs != {}:
                h = ['country', 'region', 'city', 'zip_code']
                self.__interpret_loc( ','.join([lcs[x] for x in h if x in lcs]))
        # Extract sequencing_platform
        match = re.findall(r'Platform Name: (.+)\n', qdata)
        if match:
            self['sequencing_platform'] = platforms.get(
                match[0].lower(), 'unknown'
            )
        else:
            self['sequencing_platform'] = 'unknown'
        # Extract sequencing_type
        match = re.findall(r'Library Layout: (.+)\n', qdata)
        if match:
            self['sequencing_type'] = match[0].split(',')[0].lower()
    def valid_metadata(self):
        '''
        Checks if metadata is valid
        :return: True if all mandatory fields are not ''
        '''
        for field in self.mandatory:
            if not field in self.metadata or self[field] is None or self[field] == '':
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
        self['file_names'] = files
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
                    'Geocoder error %s', query
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
