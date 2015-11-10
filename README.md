

# Download Taxonomy/Accession
Download isolates from a taxonomy tree from ENA or from a list of accessions.

## Usage
This will install the SRA tool kit if not found in the USER's path and set up the download folder for temporary *.SRA files used by fastq-dump

(make sure you select a TEMPORARY_DOWNLOAD_PATH with enough space available if you plan to download many isolates):

```bash
bash setup.sh TEMPORARY_DOWNLOAD_PATH
source env/bin/activate
bash install.sh
```

If you are using Anaconda's python distribution:

```bash
bash setup_conda.sh TEMPORARY_DOWNLOAD_PATH
source activate env
bash install.sh
```

This will install the python dependencies and create two entry points
- download-taxonomy
    ```bash
        usage: download-taxonomy [-h] [-v] [-t TAXID] [-m METADATA] -out OUTPUT

        Download script of isolates fromENA taxonomy or Accession list

        optional arguments:
          -h, --help     show this help message and exit
          -v, --version  show version number and exit
          -t TAXID       Tax ID from ENA data archive
          -m METADATA    JSON file with seed attributes and mandatory fields
          -out OUTPUT    Path to save isolates  
    ```

- download-accession-list
    ```bash
        usage: download-accession-list [-h] [-v] [-a PATH] [-m METADATA] -out OUTPUT

        Download script of isolates fromENA taxonomy or Accession list

        optional arguments:
          -h, --help     show this help message and exit
          -v, --version  show version number and exit
          -a PATH        Format: [PATH] to file containing list of ACCESSION IDs, 1
                         per line Name of the file is used to identify the isolates
                         downloaded.
          -m METADATA    JSON file with seed attributes and mandatory fields
          -out OUTPUT    Path to save isolates
    ```

Each of this programs will store each sequence inside a folder along with a metadata file.

## Examples
```bash
download-taxonomy -t 1639 -out my_folder -m meta.json
download-accession-list -a Salmonella.txt -m meta.json -out my_folder
```
## Metadata
This is the metadata attached to each of the download sequences:
```json
metadata = {
    "sample_name": "",
    "group_name": "",
    "file_names": "",
    "sequencing_platform": "",
    "sequencing_type": "",
    "pre_assembled": "",
    "sample_type": "",
    "organism": "",
    "strain": "",
    "subtype": {},
    "country": "",
    "region": "",
    "city": "",
    "zip_code": "",
    "longitude": "",
    "latitude": "",
    "location_note": "",
    "isolation_source": "",
    "source_note": "",
    "pathogenic": "",
    "pathogenicity_note": "",
    "collection_date": "",
    "collected_by": "",
    "usage_restrictions": "",
    "release_date": "",
    "email_address": "",
    "notes": "",
    "batch": "true"
}
```
In order to capture the required metadata, a file can be provided with the
following structure:

meta.json
```json
{
    "seed":{
        "pre_assembled": "no",
        "sample_type": "isolate",
        "pathogenic": "yes",
        "usage_restrictions": "public",
        "usage_delay": "0"
    },
    "mandatory": [
        "sequencing_platform",
        "sequencing_type",
        "country",
        "isolation_source",
        "collection_date"
    ]
}
```
If meta.json is not provided, these values are used by default. The result metadata will contain
the exact same seed values as provided in the meta.json file.
If the downloaded metadata doesn't contain some of the mandatory files, this isolate won't be downloaded.

## Note
This project has been set up using PyScaffold 2.4.2. For details and usage<br>
information on PyScaffold see [http://pyscaffold.readthedocs.org/](http://pyscaffold.readthedocs.org/).
