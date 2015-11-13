''' present metadata '''
import os, argparse, json

# Parse arguments
parser = argparse.ArgumentParser(
    description="Present Metadata from dowloaded samples")
parser.add_argument(
    '-d',
    dest='dir',
    metavar=('PATH'),
    help='Format: [PATH]\nto directory containing the downloaded samples.'
)
args = parser.parse_args(sys.argv[1:])

# Extract metadata from stored json files
data = []
if os.path.exists(args.dir):
    for root, dirs, files in os.walk(args.dir, topdown=False):
        if root != "":
            if root[-1] != '/': root += '/'
            for currentfile in files:
                if currentfile == 'meta.json':
                    filepath = "%s/%s"%(root, currentfile)
                    if os.path.exists(filepath):
                        with open(filepath) as f:
                            data.append(json.load(f))

# Print data as tabseparated values
head = ['sample_name', 'sequencing_platform', 'sequencing_type', 'organism',
        'strain', 'subtype', 'country', 'region', 'city', 'zip_code',
        'longitude', 'latitude', 'location_note', 'isolation_source',
        'source_note', 'collection_date', 'collected_by', 'notes']
print '\t'.join(head)
for sample in data:
    print '\t'.join([str(sample[h]) for h in head])

