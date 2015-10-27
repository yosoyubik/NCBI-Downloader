****************************************
Download Taxonomy/Accession
****************************************


Download isolates from a taxonomy tree from ENA or from a list of accessions.

Development
===========

This will install the SRA tool kit if not found in the USER's path and set up
the download folder for temporary *.SRA files used by fastq-dump::

    ./setup.sh TEMPORARY_DOWNLOAD_PATH
    source env/bin/activate
    ./install.sh

This will install the python dependencies and create two entry points

* download-taxonomy::

    usage: download-taxonomy [-h] [-v] [-t TAXID ORGANISM] -out OUTPUT
    Download script of isolates fromENA taxonomy or Accession list
    optional arguments:
      -h, --help         show this help message and exit
      -v, --version      show program's version number and exit
      -t TAXID ORGANISM  Tax ID from ENA data archive and organism associated
      -out OUTPUT        Path to store sequences and metadata
* download-accession-list::

    usage: download-accession-list [-h] [-v] [-a PATH] [-o organism] -out OUTPUT
    Download script of isolates fromENA taxonomy or Accession list
    optional arguments:
      -h, --help     show this help message and exit
      -v, --version  show program's version number and exit
      -a PATH        [PATH] to file containing list of ACCESSION IDs, 1 per line
      -o organism    This organism will be assigned to the metadata JSON file
      -out OUTPUT    Path to store sequences and metadata

Each of this programs wil store each sequence inside a folder along with a metadata file.

Examples
=======
* download-taxonomy -t Lysteria 1639 -output my_folder
* download-accession-list -a Salmonella.txt -o Salmonella -out my_folder

Note
====

This project has been set up using PyScaffold 2.4.2. For details and usage
information on PyScaffold see http://pyscaffold.readthedocs.org/.
