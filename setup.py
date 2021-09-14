from setuptools import setup
import codecs
import os.path
import pathlib


def read(filename):
    return codecs.open(filename, encoding='utf-8').read()


long_description = '\n\n'.join([read('README'),
                                read('AUTHORS'),
                                read('CHANGES')])

here = pathlib.Path(__file__).parent.resolve()

# Compile a list of companies with drivers.
drivers_path = os.path.join(here, 'lantz', 'drivers')
paths = os.listdir(drivers_path)
companies = [path for path in paths
             if os.path.isdir(os.path.join(drivers_path, path))
             and os.path.exists(os.path.join(drivers_path, path, '__init__.py'))]

setup(
    name='lantz-drivers',
    version='0.6.2',
    license='BSD 3-Clause License',
    description='Driver Library for Lantz',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/lantzproject/lantz-drivers',
    author='Hernan E. Grecco',
    author_email='hernan.grecco@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Widget Sets',
        'Topic :: System :: Hardware',
        'Topic :: System :: Hardware :: Hardware Drivers',
        'Topic :: System :: Logging',
        'Topic :: System :: Monitoring',
        'Topic :: Utilities',
    ],
    keywords='lantz, lantz-drivers, drivers, hardware drivers, hardware interface, instrumentation framework, science, research',
    packages=['lantz.drivers'] + ['lantz.drivers.' + company for company in companies],
    zip_safe=False,
    python_requires='>=3.6, <4',
    install_requires=[
        'pyserial>=3.4',
        'pyusb>=1.1.0',
        'lantzdev>=0.6',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/lantzproject/lantz-drivers/issues',
        'Source': 'https://github.com/lantzproject/lantz-drivers/',
    },
    include_package_data=True,
    options={'bdist_wheel': {'universal': '1'}},
)
