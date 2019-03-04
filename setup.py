from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

about = {}
with open(path.join(here, 'doxytag2zealdb', '__about__.py')) as fp:
    exec(fp.read(), about)

__version__ = about['__version__']
PROJECT_URL = 'https://gitlab.com/vedvyas/doxytag2zealdb'

setup(
    # TODO: move all of this metadata to doxytag2zealdb/__about__.py?
    name='doxytag2zealdb',
    version=__version__,

    description='''doxytag2zealdb creates a SQLite3 database from a Doxygen tag
    file to enable searchable Doxygen docsets with categorized entries in tools
    like helm-dash, Zeal, and Dash.''',
    long_description=open(path.join(here, 'README.md'),
                          encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    keywords='Zeal Dash Doxygen SQLite3',

    license='GPLv3+',

    author='Ved Vyas',
    author_email='ved@vyas.io',

    url=PROJECT_URL,
    download_url='%s/repository/archive.tar.bz2?ref=v%s' % (PROJECT_URL,
                                                            __version__),

    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Documentation',

        'License :: OSI Approved :: ' +
        'GNU General Public License v3 or later (GPLv3+)',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
    ],

    install_requires=[
        'docopt >= 0.6.2',
        'lxml >= 3.6.0',
        'beautifulsoup4 >= 4.4.1',
        'future'
    ],
    packages=find_packages(exclude=['docs', 'tests*']),
    package_data={
        'doxytag2zealdb': ['README.md', 'COPYING', 'CONTRIBUTORS']
    },

    entry_points={
        'console_scripts': [
            'doxytag2zealdb = doxytag2zealdb.doxytag2zealdb:main'
        ]
    }
)
