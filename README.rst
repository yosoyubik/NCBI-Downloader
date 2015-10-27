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

This will install the python dependencies and create two entry points:
* download-taxonomy::
    usage: download-taxonomy [-h] [-v] [-t TAXID ORGANISM] -out OUTPUT

    Download script of isolates fromENA taxonomy or Accession list

    optional arguments:
      -h, --help         show this help message and exit
      -v, --version      show program's version number and exit
      -t TAXID ORGANISM  Tax ID from ENA data archive and organism associated
      -out OUTPUT        Path to save isolates* download-accession-list
* download-accession-list::
    usage: download-accession-list [-h] [-v] [-a PATH] [-o organism] -out OUTPUT

    Download script of isolates fromENA taxonomy or Accession list

    optional arguments:
      -h, --help     show this help message and exit
      -v, --version  show program's version number and exit
      -a PATH        Format: [PATH] to file containing list of ACCESSION IDs, 1
                     per line Name of the file is used to identify the isolates
                     downloaded.
      -o organism    Format: [ORGANISM] to assign to all isolates
      -out OUTPUT    Path to save isolates


Examples
=======
* download-taxonomy -t Lysteria 1639 -output myDir
* download-accession-list -a input/295367.txt -o ORGANISM -out mydir

Note
====

This project has been set up using PyScaffold 2.4.2. For details and usage
information on PyScaffold see http://pyscaffold.readthedocs.org/.
