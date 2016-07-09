'''Defines the ZealDB class.'''

# Copyright (c) 2016 Ved Vyas

# This file is part of doxytag2zealdb.

# doxytag2zealdb is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# doxytag2zealdb is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with doxytag2zealdb.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import sys
import sqlite3

class ZealDB(object):
    '''
    A ZealDB object can be used to create an SQLite3 database and insert
    entries as expected by Zeal and friends. After constructing a
    ZealDB, one may make multiple calls to insert(...) in between open() and
    close() or while using the ZealDB object as a context manager. Technically,
    the context manager is reusable, and it is similarly OK to have multiple
    pairs open()+close() calls. However, doing this is currently pointless
    because the ``searchIndex'' table is dropped in open().

    Typical usage:

    with ZealDB('/path/to/db.sqlite', verbose=True) as db:
        db.insert('someName', 'someType', 'someFileName')
        ...

    db = ZealDB('/path/to/db.sqlite', verbose=True)

    db.open()
    db.insert(...)
    ...
    db.close()

    # NOTE: see point above about reuse!
    db.open()
    ...
    db.close()

    with db:
        db.insert(...)
        ...
    '''

    def __init__(self, filename, **kwargs):
        '''Initialize a ZealDB.

        A connection is not opened here. To do that, use open() or use this
        ZealDB instance as a context manager.

        Args:
            filename: A string containing full path to database file.
            **verbose: If True, extra information may be printed to stderr
                during operations.
        '''
        self.filename = filename
        self.verbose = kwargs.get('verbose', False)

        self.conn = None
        self.cursor = None

    def open(self):
        '''Open a connection to the database.

        If a connection appears to be open already, transactions are committed
        and it is closed before proceeding. After establishing the connection,
        the searchIndex table is prepared (and dropped if it already exists).
        '''
        if self.conn is not None:
            self.close()

        self.conn = sqlite3.connect(self.filename)
        self.cursor = self.conn.cursor()

        c = self.cursor
        c.execute('SELECT name FROM sqlite_master WHERE type="table"')
        if (u'searchIndex',) in c:
            c.execute('DROP TABLE searchIndex')

            if self.verbose: print('Dropped existing table', file=sys.stderr)

        c.executescript(
            '''
            CREATE TABLE searchIndex
            (id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);

            CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);
            '''
        )

    def close(self):
        '''Commit transactions and close connection if open.'''
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()

        self.cursor = None
        self.conn = None

    def __enter__(self):
        '''Enter ZealDB context. Opens a connection to the database.'''
        self.open()

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        '''Exit ZealDB context. Commits transactions and closes the database
        connection.'''
        if exc_type is not None:
            print('Exception occurred, committing changes and closing DB...',
                  file=sys.stderr)

        self.close()

    def insert(self, name, entry_type, filename):
        '''Insert an entry into the Zeal database.

        Args:
            name: A string representing the name of the entry.
            entry_type: A string representing the entry type.
            filename: A string representing the filename of the documentation
                for the entry.

        Raises:
            RuntimeError: a database connection was not established before
                calling insert()
        '''
        if self.cursor is None:
            raise RuntimeError(
                'Open DB connection before attempting to call insert!')

        db_entry = (name, entry_type, filename)

        if self.verbose:
            print('Inserting %s "%s" -> %s' % db_entry, file=sys.stderr)

        self.cursor.execute(
            '''INSERT OR IGNORE INTO searchIndex(name, type, path)
               VALUES (?, ?, ?)''', db_entry)
