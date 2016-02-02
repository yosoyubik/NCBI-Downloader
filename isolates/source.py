import os

from isolates import flipdict

# List of known platforms
platforms = {
    'illumina':         'Illumina',
    '454':              'LS454',
    'ls454':            'LS454',
    'ion torrent':      'Ion Torrent',
    'torrent':          'Ion Torrent',
    'solid':            'ABI SOLiD',
    'abi solid':        'ABI SOLiD',
    'pac bio':          'unknown',
    'pacbio':           'unknown',
    'unknown':          'unknown',
    'missing':          'unknown',
    'na':               'unknown',
    'not applicable':   'unknown',
    'not known':        'unknown'
}
sequencing_types = {
    'single':           'single',
    'paired':           'paired',
    'mate-paired':      'mate-paired',
    'unknown':          'unknown',
    'missing':          'unknown',
    'na':               'unknown',
    'not applicable':   'unknown',
    'not known':        'unknown'
}
# 'preset': (country, region, city, zip, longitude, latitude, note)
location_hash = {
    'missing': {'country': '', 'region': '', 'city': '', 'zip_code': '',
                'longitude': '', 'latitude': '', 'location_note': ''},
    'unknown': {'country': '', 'region': '', 'city': '', 'zip_code': '',
                'longitude': '', 'latitude': '', 'location_note': ''},
    'na':      {'country': '', 'region': '', 'city': '', 'zip_code': '',
                'longitude': 30.7956597, 'latitude': 26.8357675,
                'location_note': 'egypt'},
    'egypt':   {'country': 'Egypt', 'region': '', 'city': '', 'zip_code': '',
                'longitude': '', 'latitude': '', 'location_note': ''},
    'usa:or':  {'country': 'United States', 'region': 'Oregon', 'city': '',
                'zip_code': '', 'longitude': -120.5380993,
                'latitude': 44.1419049, 'location_note': 'USA:OR'}
}

acctypes = flipdict({ # flipdict reverses the dictionary!
    'study':        ['PRJ', 'SRP', 'ERP', 'DRP'],
    'sample':       ['SAM', 'SRS', 'ERS', 'DRS'],
    'experiment':   ['SRX', 'ERX', 'DRX'],
    'run':          ['SRR', 'ERR', 'DRR']
})

# Read Ontology DB from file to dict
ontology = []
try: ontology_fp = os.path.dirname(os.path.abspath(__file__))+'/etc/source_ontology.csv'
except: print "Could not set Ontology path!"
else:
    if os.path.exists(ontology_fp):
        ontology.append({})
        with open(ontology_fp) as f:
            for l in f:
                l = l.strip()
                if l == '': continue
                if l[0] == '#':
                    if len(l) > 3 and l[:3] == '###':
                        # Start new ontology dictionary
                        ontology.append({})
                    continue
                if not ',' in l: continue
                tmp = l.split(',')
                if not tmp[0] in ontology[-1]:
                    ontology[-1][tmp[0]] = tmp[1:]
                else: print "Ontology doublicate found! Please fix (%s)"%tmp[0]
    else:
        print "Ontology file could not be found: %s"%ontology_fp
