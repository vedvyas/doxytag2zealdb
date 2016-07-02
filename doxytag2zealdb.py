#!/usr/bin/python
'''
doxytag2zealdb: creates a SQLite3 database from a Doxygen tag file to enable
searchable Doxygen docsets with categorized entries in tools like helm-dash
[1], Zeal [2], and Dash [3]

Copyright (c) 2016 Ved Vyas

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Usage:
  doxytag2zealdb.py [-v] --tag FILENAME --db FILENAME
  doxytag2zealdb.py (-h | --help)

Options:
  -h --help       Show this screen
  --tag FILENAME  Input Doxygen tag file to process
  --db FILENAME   Output SQlite3 database
  -v --verbose    Print further information while processing the tag file

See the README for further information on how to use doxytag2zealdb while
preparing docsets from Doxygen output.

References:
[1]: https://github.com/areina/helm-dash
[2]: https://github.com/zealdocs/zeal
[3]: https://kapeli.com/dash
'''

from __future__ import print_function
import sys
import sqlite3
from bs4 import BeautifulSoup
from docopt import docopt

if __name__ == '__main__':
    args = docopt(__doc__, version='doxytag2zealdb v0.1')

    verbose = args.get('--verbose', False)
    tag_filename = args['--tag']
    db_filename = args['--db']

    entry_count = 0

    conn = sqlite3.connect(db_filename)
    c = conn.cursor()

    c.execute('SELECT name FROM sqlite_master WHERE type="table"')
    if (u'searchIndex',) in c:
        c.execute('DROP TABLE searchIndex')

        if verbose: print('Dropped existing table', file=sys.stderr)

    c.execute('''CREATE TABLE searchIndex
                 (id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT)''')

    c.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path)')

    with open(tag_filename, 'r') as tag_file:
        soup = BeautifulSoup(tag_file, 'lxml-xml')

    # First pass: "compound" tags that are pretty straightforward to
    # handle. Some tag "kind"s are not handled.
    for doxygen_kind in [
            u'class',
            # u'dir',
            u'file',
            # u'group',
            u'namespace',
            # u'page',
            u'struct',
            u'union'
    ]:
        zeal_entry_type = doxygen_kind.capitalize()

        for entry in soup.findAll(name='compound',
                                  attrs={'kind': doxygen_kind}):
            # Note: due to conflict between tag.name and an actual tag named
            # "name", using findChild('name')
            zeal_entry_name = entry.findChild('name').contents[0]

            doxygen_filename = entry.filename.contents[0]
            if doxygen_kind == u'file': doxygen_filename += '.html'

            db_entry = (zeal_entry_name, zeal_entry_type, doxygen_filename)

            if verbose:
                print('Inserting %s "%s" -> %s' % (
                    zeal_entry_type, zeal_entry_name, doxygen_filename),
                      file=sys.stderr)

            c.execute('''INSERT OR IGNORE INTO searchIndex(name, type, path)
                         VALUES (?, ?, ?)''', db_entry)
            entry_count += 1

    # Second pass: "member" tags. Various transformations may be needed
    # depending on the tag "kind".
    for doxygen_kind in [
            u'function',
            u'define',
            u'enumeration',
            u'enumvalue',
            u'typedef',
            u'variable'
    ]:
        zeal_entry_type = doxygen_kind.capitalize()

        if doxygen_kind == u'enumeration':
            zeal_entry_type = u'Enum'
        elif doxygen_kind == u'enumvalue':
            zeal_entry_type = u'Value'
        elif doxygen_kind == u'typedef':
            zeal_entry_type = u'Type'

        for entry in soup.findAll(name='member', attrs={'kind': doxygen_kind}):
            # Note: due to conflict between tag.name and an actual tag named
            # "name", using findChild('name')
            zeal_entry_name = entry.findChild('name').contents[0]

            # Use (partially-) qualified names for members of classes, etc.
            parent_entry = entry.findParent()
            if parent_entry.get('kind') in ['class', 'struct', 'namespace']:
                zeal_entry_name = ''.join(
                    [parent_entry.findChild('name').contents[0], '::',
                     zeal_entry_name])

            # Use an entry type of "method" for class methods
            if doxygen_kind == u'function' and parent_entry.get('kind') in [
                    'class', 'struct']:
                zeal_entry_type = u'Method'

            # Include function/method arguments and return type
            if doxygen_kind == u'function':
                func_args = entry.findChild('arglist')
                if args and len(func_args.contents):
                    zeal_entry_name += func_args.contents[0]

                ret_type = entry.findChild('type')
                if ret_type and len(ret_type.contents):
                    zeal_entry_name += ' -> ' + ret_type.contents[0]

            doxygen_filename = '#'.join([entry.anchorfile.contents[0],
                                         entry.anchor.contents[0]])

            db_entry = (zeal_entry_name, zeal_entry_type, doxygen_filename)

            if verbose:
                print('Inserting %s "%s" -> %s' % (
                    zeal_entry_type, zeal_entry_name, doxygen_filename),
                      file=sys.stderr)

            c.execute('''INSERT OR IGNORE INTO searchIndex(name, type, path)
                         VALUES (?, ?, ?)''', db_entry)
            entry_count += 1

    if verbose:
        print('Inserted %d entries' % entry_count, file=sys.stderr)

    conn.commit()
    conn.close()
