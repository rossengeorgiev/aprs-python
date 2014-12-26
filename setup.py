from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
__version__ = open('aprslib/version.py').read().split("'")[1]

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='aprslib',
    version=__version__,
    description='Module for accessing APRS-IS and parsing APRS packets',
    long_description=long_description,
    url='https://github.com/rossengeorgiev/aprs-python',
    author='Rossen Georgiev',
    author_email='zx.devel@gmail.com',
    license='GPLv2',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Communications :: Ham Radio',
    ],
    test_suite='tests',
    keywords='aprs aprslib parse parsing aprs-is library base91',
    packages=['aprslib'],
    install_requires=[],
    zip_safe=False,
)
