#!/bin/env bash

#
# This will install the SRA tool kit if not found in the USER's path and set up
# the download folder for temporary *.SRA files.
#


SRAURL="//ftp-trace.ncbi.nlm.nih.gov/sra/sdk/current/sratoolkit.current-centos_linux64.tar.gz"
# Path where temporaru SRA files will be stored
TEMPDOWNLOAD=$1
# Creates a virtual environment
virtualenv env
# Install SRA toolkit
command -v fastq-dump >/dev/null 2>&1 || {
    echo 'Installing sratoolkit...'
    echo "OS type: ${OSTYPE}"

    if [[ "${OSTYPE}" == 'linux'* ]]; then
        wget ${SRAURL}
        tar -xzf sratoolkit.current-centos_linux64.tar.gz
        ln -s ./sra-toolkit/fastq-dump env/bin/fast-dump
    elif [[ "${OSTYPE}" == 'darwin'* ]]; then
        brew install homebrew/science/sratoolkit
    else
        curl -L ${SRAURL} | bash
        tar -xzf sratoolkit.current-centos_linux64.tar.gz
        ln -s ./sra-toolkit/fastq-dump bin/fast-dump
    fi
    vdb-config --set repository/user/main/public/root=${TEMPDOWNLOAD}
}
