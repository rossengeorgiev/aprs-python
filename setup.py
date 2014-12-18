from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
__version__ = open('aprs/version.py').read().split("'")[1]

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='aprs',
    version=__version__,
    description='Library for working with APRS',
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
    setup_requires=['pypandoc'],
    test_suite='tests',
    keywords='aprs parse parsing aprs-is library base91',
    packages=['aprs'],
    install_requires=[],
    zip_safe=False,
)
