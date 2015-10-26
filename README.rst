=============
Download Taxonomy/Accession
=============


Add a short description here!


Description
===========

Download isolates from a taxonomy tree from ENA or from a list of accessions.

Development
===========
```bash
./setup.sh TEMPORARY_DOWNLOAD_PATH
```
This will install the SRA tool kit if not found in the USER's path and set up
the download folder for temporary *.SRA files used by fastq-dump

After you should activate the new environment by typing:
```bash
source env/bin/activate
```

```bash
./install.sh
```
This will install the python dependencies and create two entry points:
* download-taxonomy
        usage: download-taxonomy [-h] [-v] [-t TAXID ORGANISM] -output OUTPUT
* download-accession-list
        usage: download-accession-list [-h] [-v] [-a BIOPROJECTID ORGANISM PATH] -output OUTPUT


Examples
=======
download-taxonomy -t Lysteria 1639 -output myDir
download-accession-list -a input/295367.txt -output mydir

Note
====

This project has been set up using PyScaffold 2.4.2. For details and usage
information on PyScaffold see http://pyscaffold.readthedocs.org/.
