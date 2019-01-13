import os
import sys

if (sys.version_info < (3, 6)):
    print("Python 3.6 or higher is required, please see https://www.python.org/ or your OS package repository",
          file=sys.stderr)
    sys.exit(2)

from setuptools import setup, find_packages

long_desc = open('README.md').read()

if os.path.exists('README.rst'):
    long_desc = open('README.rst').read()

setup(
    name='skutter',
    version='0.3',
    packages=find_packages(),
    scripts=['bin/skutter'],
    entry_points={
        'skutter.plugins.checks': [
            'process=skutter.checks:Process',
        ],
        'skutter.plugins.actions': [
            'iptables=skutter.actions:IPTables',
        ]
    },

    license='GNU GPL v3',
    long_description=long_desc,

    author="Adam Bishop",
    author_email="adam@omega.org.uk",
    description="Skutter is a daemon for executing menial tasks.",
    url="https://github.com/TheMysteriousX/skutter",

    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.7',
    ],
)
