#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

'''
import re
import json
import geocoder
from datetime import datetime

from isolates import mail, openurl, ceil
from isolates.log import _logger
from isolates.source import (acctypes, ontology, platforms, sequencing_types,
                             location_hash)
from isolates.template import (metadata as metadata_template,
                               default as default_metadata)

class metadata_obj(object):
    ''' This class describes metadata associated with a sample '''
    # Global Class Variables (shared across instances)
    new_ontologies = {}
    def __init__(self, accession, settings=None):
        if settings is None: settings = default_metadata
        self.metadata = metadata_template
        self.metadata.update(settings["seed"])
        self.mandatory = settings['mandatory']
        self.accessions = {'query': accession}
        # Set metadata collection site URL
        ncbi = 'http://www.ncbi.nlm.nih.gov'
        self.sra_url1 = ('%s/Traces/sra/sra.cgi?'
                         'save=efetch&'
                         'db=sra&'
                         'rettype=runinfo&'
                         'term=%s')%(ncbi, '%s')
        self.sra_url2 = '%s/sra/?term=%s&format=text'%(ncbi, '%s')
        self.bio_url = '%s/biosample/?term=%s&format=text' %(ncbi, '%s')
        # Extract Sample Metadata
        self.ExtractData(accession)
    def __getitem__(self, key):
        return self.metadata[key]
    def __setitem__(self, key, value):
        self.metadata[key] = value
    def ExtractData(self, query):
        ''' Extract Sample Metadata '''
        new_platforms = []
        new_seqtypes = []
        # New approach using runinfo list
        with openurl(self.sra_url1%(query)) as u:
            headers = u.readline().split(',')
            indexes = [(x, headers.index(x)) for x in ["Run", "Experiment",
                "Sample", "SRAStudy", "BioSample", "Platform", "LibraryLayout",
                "SampleName", "ScientificName", "CenterName"]]
            for l in u:
                l = l.strip()
                if l == '': continue
                if l[0] == '#': continue
                d = l.split(',')
                self.accessions['run'] = d[indexes[0][1]]
                self.accessions['experiment'] = d[indexes[1][1]]
                self.accessions['sample'] = d[indexes[2][1]]
                self.accessions['study'] = d[indexes[3][1]]
                self.accessions['biosample'] = d[indexes[4][1]]
                platform = d[indexes[5][1]].lower()
                if platform in platforms:
                    self['sequencing_platform'] = platforms[platform]
                else:
                    self['sequencing_platform'] = 'unknown'
                    if not platform in new_platforms:
                        new_platforms.append(platform)
                seqtype = d[indexes[6][1]].lower()
                if seqtype in sequencing_types:
                    self['sequencing_type'] = sequencing_types[seqtype]
                else:
                    self['sequencing_type'] = 'unknown'
                    if not seqtype in new_seqtypes:
                        new_seqtypes.append(seqtype)
                self['sample_name'] = d[indexes[7][1]]
                self['organism'] = d[indexes[8][1]]
                self['collected_by'] = d[indexes[9][1]]
                self['biosample'] = self.accessions['biosample']
                break # Just use the first entry!
                # Should be fixed to handle different query sequences!!!
        with openurl(self.sra_url2%(query)) as u: qdata = u.read()
        # Extract sample attributes
        match = re.findall(r'Sample Attributes: (.+)\n', qdata)
        lcs = {} # location parts
        host = None
        source = None
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
                    source = val
                elif att in ['host', 'specific_host', 'specific host']:
                    host = val
                elif att == 'BioSample':
                    self['biosample'] = val
                elif att in ['collection_date', 'collection date']:
                    self['collection_date'] = self.__format_date(
                        *self.__interpret_date(val)
                    )
                    if self['collection_date'] == '':
                        _logger.warning(
                            'Date Empty: %s, %s',
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
        # Handle Isolation source
        cats = []
        if host is not None:
            for d in ontology:
                cats = [d[k][0] for k in d.keys() if k in host.lower()]
                if cats:
                    break
        if (not cats or cats[0] == 'unknown') and source is not None:
            for d in ontology:
                cats = [d[k][0] for k in d.keys() if k in source.lower()]
                if cats:
                    break
        if cats:
            self['isolation_source'] = cats[0]
            _logger.warning(
                'Source identified: %s (%s, %s), %s',
                self['isolation_source'], host, source, query
            )
        else:
            if host is None:
                host = 'unknown'
            elif host not in self.new_ontologies:
                self.new_ontologies[host] = query
            if source is None:
                source = 'unknown'
            elif source not in self.new_ontologies:
                self.new_ontologies[source] = query
            _logger.warning(
                'Source not identified: (%s, %s), %s',
                host, source, query
            )
        self['source_note'] = source
        
        # Extract Run IDs associated with the sample
        #Run #1: ERR276921, 1356661 spots, 271332200 bases
        self.runIDs = re.findall(r'Run #\d+: (.+?),.+', qdata)
        # Notify Curators By Email
        if mail is not None:
            if len(self.new_ontologies)>0:
                _logger.debug(mail.test(
                    'New isolation source...',
                    'Sources not identified:\n%s\n'%(
                        '\n'.join([', '.join(e) for e in self.new_ontologies.items()]))
                    ))
                mail.send(
                    'New isolation source...',
                    'Sources not identified:\n%s\n'%(
                        '\n'.join([', '.join(e) for e in self.new_ontologies.items()]))
                    )
            if len(new_platforms)>0:
                _logger.debug(mail.test(
                    'New platforms...',
                    'Platforms not accounted for:\n%s\n'%(
                        '\n'.join(new_platforms))
                    ))
                mail.send(
                    'New platforms...',
                    'Platforms not accounted for:\n%s\n'%(
                        '\n'.join(new_platforms))
                    )
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
        with open('%s/meta.json' % dir, 'w') as f:
            f.write(json.dumps(self.metadata, ensure_ascii=False).encode('utf-8'))
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
                if g.status != 'OK':
                    if ',' in val:
                        # Try with only country
                        val2 = val.split(',')[0]
                        _logger.warning(
                            ('Geocoder failed (%s)!,'
                             'trying with country only... (%s)'), val, val2)
                        g = geocoder.google(val2)
                        if g.status != 'OK':
                            raise Exception(g.status)
                    else:
                        raise Exception(g.status)
            except Exception, e:
                _logger.warning('Geocoder error %s', query)
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

def ExtractExperimentMetadata(accession, json=None):
    # Extract sample metadata
    m = metadata_obj(accession, json)
    return m

def ExtractExperimentIDs_acc(sample_accession):
    ''' Extract experiments which have runs associated
    >>> ExtractExperimentIDs_acc('ERS397989')
    ['ERX385098']
    >>> ExtractExperimentIDs_acc('SRS331977')
    ['SRX146831', 'SRX365746', 'SRX146834', 'SRX146829', 'SRX146822', 'SRX146814', 'SRX146806']
    '''
    experiments = {}
    sra_url = 'http://www.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&db=sra&rettype=runinfo&term=%s'
    with openurl(sra_url%(sample_accession)) as u:
        headers = u.readline()
        try:
            idx = headers.split(',').index("Experiment")
        except:
            print headers
        else:
            for l in u:
                l = l.strip()
                if l == '': continue
                if l[0] == '#': continue
                exp = l.split(',')[idx].strip()
                if not exp in experiments: experiments[exp] = 1
    return experiments.keys()

def ExtractExperimentIDs_tax(taxid):
    ''' Extract experiments which have runs associated from taxid
    >>> ExtractExperimentIDs_tax('211968')
    ['SRX1308653', 'SRX1308716', 'SRX1308789', 'SRX1308879', 'SRX337751']
    '''
    ena_url = ('http://www.ebi.ac.uk/ena/data/warehouse/search?'
               'query="tax_tree(%s)"&'
               'result=read_experiment')%(taxid)
    countquery = '&resultcount'
    display = '&display=report&fields=experiment_accession'
    # Find number of entries for the provided taxid 
    count = 0
    with openurl(ena_url+countquery) as u:
        for l in u:
            l = l.strip()
            if ':' in l:
                tmp = l.split(':')
                if tmp[0] == 'Number of results':
                    count = int(tmp[1].replace(',',''))
    # Extract experiment IDs
    experiments = []
    if count > 0:
        length = 100000
        pages = ceil(count/float(length))
        for p in xrange(pages):
            page_offset = '&offset=%s&length=%s'%(p*length+1, length)
            with openurl(ena_url+display+page_offset) as u:
                header = u.readline()
                for l in u:
                    l = l.strip()
                    if l[:3] in acctypes and acctypes[l[:3]] == 'experiment':
                        experiments.append(l)
                    else:
                        print("Unknown Experiment ID: %s (taxid=%s)"%(l,taxid))
    return experiments

def ExtractTaxIDfromSearchTerm(query):
    ''' Extract taxonomy ID from NCBI taxonomy search
    >>> ExtractTaxIDfromSearchTerm('Salmonella')
    590
    '''
    ncbi_url = 'http://www.ncbi.nlm.nih.gov/taxonomy/?term=%s&report=taxid'%(
        query)
    # Find number of entries for the provided taxid 
    taxid = None
    with openurl(ncbi_url) as u:
        for l in u:
            # remove html tags
            l = re.sub('<.+?>', '', l)
            l = l.strip()
            if l == '': continue
            try: taxid = int(l)
            except: print("Error: Unhandled result from taxid search! (%s)"%l)
    return taxid
