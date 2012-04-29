#! /usr/bin/env python

import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

VERSION = [l for l in read('tastypie_client/__init__.py').splitlines()
           if l.startswith('__version__ =')][0].split("'")[1]

setup(
    name='tastypie-client',
    version=VERSION,
    packages=find_packages(),
    author='Philippe Muller',
    author_email='philippe.muller@cfm.fr',
    description='Client for Django-Tastypie based REST services',
    long_description=read('README.rst'),
    keywords='tastypie rest django requests',
    install_requires=['requests>=0.11.2'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
