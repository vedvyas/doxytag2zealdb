'''Defines the TagfileProcessor class.'''

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
from bs4 import BeautifulSoup

from doxytag import *

class TagfileProcessor(object):
    '''
    A TagfileProcessor object can be used to run through a Doxygen-generated
    tag file and insert entries into a Zeal database (via ZealDB). It depends
    on TagProcessors to find tags of interest in the file and extract the
    necessary information from them for insertion into the DB. During
    initialization, a handful of TagProcessors are registered for automatic use
    during a call to process().

    TagfileProcessor manages the BeautifulSoup object used to traverse the tag
    file. It passes this soup and individual tags to TagProcessors to work
    with.

    Typical usage:

    with ZealDB(db_filename, verbose=verbose) as db:
        with open(tag_filename, 'r') as tag:
            tagfile_proc = TagfileProcessor(tag, db, verbose=verbose)
            tagfile_proc.process()
    '''

    def __init__(self, file_obj, zeal_db, **kwargs):
        '''Initialize a tag file processor.

        Args:
            file_obj: A file-like object to read the tags from.
            zeal_db: A ZealDB instance that should be open() by the time
                process is called on this instance.
            **verbose: If True, extra information may be printed to stderr
                during operations.
            **kwargs: **verbose and other keyword arguments _may_ be passed on
                to TagProcessors that are registered in
                init_tag_processors(). Refer to that method and various
                TagProcessor initializers to see which keyword arguments are
                useful.
        '''
        self.soup = BeautifulSoup(file_obj, 'lxml-xml')
        self.zeal_db = zeal_db

        self.opts = kwargs
        self.verbose = kwargs.get('verbose', False)

        self.entry_count = 0

        self.tag_procs = {}
        self.init_tag_processors()

    def init_tag_processors(self):
        '''Register the TagProcessors that are bundled with doxytag2zealdb.'''
        register = self.register_tag_processor

        register('class', classTagProcessor(**self.opts))
        register('file', fileTagProcessor(**self.opts))
        register('namespace', namespaceTagProcessor(**self.opts))
        register('struct', structTagProcessor(**self.opts))
        register('union', unionTagProcessor(**self.opts))
        register('function', functionTagProcessor(**self.opts))
        register('define', defineTagProcessor(**self.opts))
        register('enumeration', enumerationTagProcessor(**self.opts))
        register('enumvalue', enumvalueTagProcessor(**self.opts))
        register('typedef', typedefTagProcessor(**self.opts))
        register('variable', variableTagProcessor(**self.opts))

    def register_tag_processor(self, name, tag_processor):
        '''Register a tag processor.

        Args:
            name: A string to help keep track of the tag processor. Used as a
                key to access the tag processor.
            tag_processor: A TagProcessor instance to associate with ``name''.
        '''
        self.tag_procs[name] = tag_processor

    def unregister_tag_processor(self, name):
        '''Unregister a tag processor.

        Args:
            name: A string key that maps to the TagProcessor to unregister.
        '''
        if name in self.tag_procs:
            del self.tag_procs[name]

    def process(self):
        '''Run all tag processors.'''
        for tag_proc in self.tag_procs:
            before_count = self.entry_count
            self.run_tag_processor(tag_proc)
            after_count = self.entry_count

            if self.verbose:
                print('Inserted %d entries for "%s" tag processor' % (
                    after_count - before_count, tag_proc), file=sys.stderr)

        if self.verbose:
            print('Inserted %d entries overall' % self.entry_count,
                  file=sys.stderr)

    def run_tag_processor(self, tag_proc_name):
        '''Run a tag processor.

        Args:
            tag_proc_name: A string key that maps to the TagProcessor to run.
        '''
        tag_processor = self.tag_procs[tag_proc_name]

        for tag in tag_processor.find(self.soup):
            self.process_tag(tag_proc_name, tag)

    def process_tag(self, tag_proc_name, tag):
        '''Process a tag with a tag processor and insert a DB entry.

        Args:
            tag_proc_name: A string key that maps to the TagProcessor to use.
            tag: A BeautifulSoup Tag to process.
        '''
        tag_processor = self.tag_procs[tag_proc_name]

        db_entry = (tag_processor.get_name(tag),
                    tag_processor.get_entry_type(tag),
                    tag_processor.get_filename(tag))

        self.zeal_db.insert(*db_entry)

        self.entry_count += 1
