#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

import os
import codecs


def read(filename):
    return codecs.open(filename, encoding='utf-8').read()


long_description = '\n\n'.join([read('README'),
                                read('AUTHORS'),
                                read('CHANGES')])

__doc__ = long_description

root_folder = os.path.dirname(os.path.abspath(__file__))

# Compile a list of companies with drivers.
folder = os.path.join(root_folder, 'lantz', 'drivers')
paths = os.listdir(folder)
companies = [path for path in paths
             if os.path.isdir(os.path.join(folder, path))
             and os.path.exists(os.path.join(folder, path, '__init__.py'))]


setup(name='lantz-drivers',
      version='0.5.2',
      license='BSD',
      description='Instrumentation framework',
      long_description=long_description,
      keywords='measurement control instrumentation science',
      author='Hernan E. Grecco',
      author_email='hernan.grecco@gmail.com',
      url='https://github.com/lantzproject',
      packages=['lantz.drivers'] + ['lantz.drivers.' + company for company in companies],
      install_requires=['lantz-core>=0.5',
                        ],
      zip_safe=False,
      platforms='any',
      classifiers=[
           'Development Status :: 4 - Beta',
           'Intended Audience :: Developers',
           'Intended Audience :: Science/Research',
           'License :: OSI Approved :: BSD License',
           'Operating System :: MacOS :: MacOS X',
           'Operating System :: Microsoft :: Windows',
           'Operating System :: POSIX',
           'Programming Language :: Python',
           'Programming Language :: Python :: 3.2',
           'Programming Language :: Python :: 3.3',
           'Programming Language :: Python :: 3.4',
           'Topic :: Scientific/Engineering',
           'Topic :: Software Development :: Libraries'
      ],
)
