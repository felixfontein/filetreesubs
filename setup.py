"""File Tree Subs"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='filetreesubs',
    version='1.0.0',
    description='Synchronize a file tree with text file substitutions',
    long_description=long_description,
    url='https://github.com/felixfontein/filetreesubs',
    author='Felix Fontein',
    author_email='felix@fontein.de',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Text Processing',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='synchronization substitution',
    packages=find_packages(),
    install_requires=['doit>=0.28.0', 'setuptools>=20.3'],
    entry_points={
        'console_scripts': [
            'filetreesubs = filetreesubs.__main__:main',
        ],
    },
)
