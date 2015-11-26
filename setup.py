#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Setup file for isolates.

    This file was generated with PyScaffold 2.4.2, a tool that easily
    puts up a scaffold for your new Python project. Learn more under:
    http://pyscaffold.readthedocs.org/
"""
import sys
import os
from setuptools import setup

def setup_package():
    needs_sphinx = {'build_sphinx', 'upload_docs'}.intersection(sys.argv)
    sphinx = ['sphinx'] if needs_sphinx else []
    setup(setup_requires=['six', 'pyscaffold>=2.4rc1,<2.5a0'] + sphinx,
          tests_require=['pytest_cov', 'pytest'],
          use_pyscaffold=True)

def install_shell_scripts():
    repo_dir = os.path.dirname(os.path.realpath(__file__))
    print repo_dir +"/env/bin/update", repo_dir +"/update"
    # if not os.path.exists(repo_dir +"/env/bin/update"):
        # os.symlink(repo_dir +"/update", repo_dir +"/env/bin/")

if __name__ == "__main__":
    setup_package()
    install_shell_scripts()
