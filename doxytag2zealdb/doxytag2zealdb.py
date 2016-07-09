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
                    [--include-parent-scopes]
                    [--include-function-signatures]
  doxytag2zealdb.py (-h | --help)

Options:
  -h --help                      Show this screen
  --tag FILENAME                 Input Doxygen tag file to process
  --db FILENAME                  Output SQlite3 database
  -v --verbose                   Print further information while processing the
                                 tag file
  --include-parent-scopes        Include parent scope in entry names
  --include-function-signatures  Include function arguments and return types in
                                 entry names

See the README for further information on how to use doxytag2zealdb while
preparing docsets from Doxygen output.

References:
[1]: https://github.com/areina/helm-dash
[2]: https://github.com/zealdocs/zeal
[3]: https://kapeli.com/dash
'''

from __future__ import print_function

from docopt import docopt

from doxytagfile import TagfileProcessor
from zealdb import ZealDB

def main():
    args = docopt(__doc__, version='doxytag2zealdb v0.1')

    verbose = args.get('--verbose', False)
    tag_filename = args['--tag']
    db_filename = args['--db']

    # Prepare keyword arguments that should propagate all the way to
    # TagProcessors
    opts = {}
    for opt in [
            '--include-parent-scopes',
            '--include-function-signatures'
    ]:
        # Make valid kwarg names by stripping leading '-'s or '--'s and
        # replacing other '-'s with underscores
        opt_kwarg_name = opt.strip('-').replace('-', '_')

        # Pass whatever docopt reports, not just if it's non-False
        opts[opt_kwarg_name] = args[opt]

    with ZealDB(db_filename, verbose=verbose) as zdb:
        with open(tag_filename, 'r') as tag:
            tagfile_proc = TagfileProcessor(tag, zdb, verbose=verbose, **opts)
            tagfile_proc.process()

if __name__ == '__main__':
    main()
