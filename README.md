doxytag2zealdb
==============

doxytag2zealdb creates a SQLite3 database from a Doxygen tag file to enable
searchable Doxygen docsets with categorized entries in tools like
[helm-dash][1], [Zeal][2], and [Dash][3].

## Introduction ##

[Doxygen's `GENERATE_DOCSET`][4] configuration option does most of the work to get a
usable docset for use with helm-dash and friends. However, one still has to
write a SQLite3 database to facilitate searching and browsing by entry type.

doxytag2zealdb uses [Beautiful Soup][5] to traverse Doxygen tag files, then extracts
and prepares entries to write to the DB as suggested in the
[Dash guide on generating docsets][6].

doxytag2zealdb has been developed against the Doxygen tag file output for a few
C++ codebases. At present:

- Several Doxygen tag file entry types are mapped to their corresponding docset
  entry types. There may be more mapping opportunities to the [entry types][7]
  in the docset generation guide. 
- Some behavior is hard-coded, like 1) the inclusion of function arguments and
  return types in entry names and 2) (partially-) qualified names for
  class/struct/namespace members. It probably makes sense to add some options
  to control this behavior and make the processing more extensible.

## Typical Usage ##

1. Suppose you have a project named `foo` with Doxygen configuration in
   `foo.dox`. As suggested in the
   [Doxygen section of the Dash docset guide][8], at least make sure
   `GENERATE_DOCSET = yes` in `foo.dox`. Ensure HTML output is enabled and
   specify tag file generation with
   `GENERATE_TAGFILE = /path/to/desired/foo.tag`. You may wish to further
   customize `DOCSET_BUNDLE_ID` (which controls the name of the docset
   subdirectory), other `DOCSET_*` options, and the other options mentioned in
   the guide.

2. If the top-level Doxygen output directory is `output`, go to `output/html/`
   and run `make`. An error about missing `docsetutil` is fine (and expected
   when not using OS X).

3. The SQLite DB is expected to be named docSet.dsidx and placed in the
   directory `output/html/$(DOCSET_BUNDLE_ID).docset/Contents/Resources/`,
   where `$(DOCSET_BUNDLE_ID)` may be something like `org.doxygen.Project` if
   left uncustomized in `foo.dox`. This is where doxytag2zealdb comes in:
   
        doxytag2zealdb.py --tag /path/to/desired/foo.tag \
          --db /path/to/output/html/$(DOCSET_BUNDLE_ID).docset/Contents/Resources/docSet.dsidx

4. After adding an icon and whatever else,
   `output/html/$(DOCSET_BUNDLE_ID).docset` should be ready to use with the
   tool of your choice.

## License ##

doxytag2zealdb is distributed under the terms of the GNU General Public License
version 3 or (at your option) any later version. Please see COPYING.

[1]: https://github.com/areina/helm-dash
[2]: https://github.com/zealdocs/zeal
[3]: https://kapeli.com/dash
[4]: http://www.stack.nl/~dimitri/doxygen/manual/config.html#cfg_generate_docset
[5]: https://www.crummy.com/software/BeautifulSoup
[6]: https://kapeli.com/docsets#createsqlite
[7]: https://kapeli.com/docsets#supportedentrytypes
[8]: https://kapeli.com/docsets#doxygen
