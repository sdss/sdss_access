.. _sdss_access-changelog:

==========
Change Log
==========

This document records the main changes to the sdss_access code.

1.1.0 (2020-07-07)
------------------
- Feature :issue:`7` - Adds a progress bar to downloads with `tqdm`
- Feature :issue:`18` - Allow Path to work off of loaded module files
- Bug Fix: issue appending compression suffixes when wildcards present

1.0.1 (2020-05-28)
------------------

- Bug Fix :issue:`16` - HttpAccess used in public mode checks for netrc file
- Combines separate `set_auth` methods in `BaseAccess` and `HttpAccess` into a single `set_auth` available as `AuthMixin`
- `Auth.set_netrc` now raises an `AccessError` on failure to find a value netrc file.

1.0.0 (2020-05-07)
------------------

Refactored
^^^^^^^^^^
- Modified sdss_access to use the new versioned tree.  Removes input and dependency on single `sdss_paths.ini` file.
- sdss_access no longer uses ConfigParser to parse the `sdss_paths.ini` file
- path templates are passed in directly from the `tree` python product
- The symbol for "special function" path definition has changed from `%` to `@`
- `sdss_access` now checks for compressed/uncompressed files on disk compared to its path template definition
- remote access classes, i.e `RsyncAaccess`, no longer need both public and release to be specified to access DRs.  Sets public=True automatically if `DR` in release name.
- Added ``path.changelog`` module with new ``compute_changelog`` and ``get_path_templates`` functions to compute changes in paths between releases
- Moved tests out of ``sdss_access`` python package to top level.
- Deprecated included logger and config in favor of ``sdsstools`` logger and config.
- Simplified python package setup.cfg and consolidated requirements files

0.2.11 (2020-05-07)
-------------------

- Pinning sdss-tree requirement to <3.0

0.2.10 (2020-04-23)
-------------------

Fixed
^^^^^
- Bug in remote file existence check for following redirects.

0.2.9 (2019-12-06)
------------------

Fixed
^^^^^
- bug in rtfd build failures
- Issue :issue:`12` - bug on Windows when HOME drive different than Window temporary directory drive
- Issue :issue:`11` - bug on Windows not creating temporary paths correctly

0.2.8 (2019-11-12)
------------------

Added
^^^^^
- new extract method to return extracted keywords from a given filename
- new tests for sdss_access.path
- methods to extract and look up source code given a method name
- sdss_access now has a `CurlAccess` class to enable use on Windows OS
- implemented new `BaseAccess` class to abstract out commonalities between `RsyncAccess` and `CurlAccess`
- added a general `Access` class which handles the choice between `Rsync/CurlAccess`
- issue :issue:`10` - added public access for `HttpAccess`
- merged PR :pr:`6` - add curl as an access method

Changed
^^^^^^^
- expanded lookup_keys to also look for keywords inside special % functions
- moved special function template substitution into a separate method
- replaced template envvar substitution with os.path.expandvars
- updating yaml.load to use FullLoaded in compliance with pyyaml 5.1
- changing disutils.strictversion to parse_versions
- moved methods from RsyncAccess and CurlAccess into common BaseAccess
- refactored the test suite to add tests on DR data, and simplify new path entries

Fixed
^^^^^
- Bug fix for pathlib on 2.7 python systems
- Issue :issue:`9` Bug fix in generate_stream_task for public rsync locations

0.2.7 (2018-09-06)
------------------

Added
^^^^^
* Ability to check for a remote file existence on the SAS

Changed
^^^^^^^
* rsync.reset now resets both the initial stream and the real stream
* rsync.add now accepts the full keyword argument
* rsync.full now checks for itself in kwargs and returns that

0.2.6 (2018-07-10)
------------------

Fixed
^^^^^
* Bug when checking for missing keys; removes key format from variable name


0.2.5 (2018-07-09)
------------------

Added
^^^^^
* New tests for Path and RsyncAccess
* Public toggling (now replants Tree upon init of Path or RsyncAccess)
* lookup_names method to look up all the available sdss_path names

Changed
^^^^^^^
* Wrapped config file opens in 'with' to ensure proper file closures
* Cleaned up some verbose warnings
* Accessing a 'full' keyword argument in Path methods to ensure proper handling
* path generation now fails with KeyError when missing input keyword arguments

Fixed
^^^^^
* Bug with RsyncAccess not properly working with public data releases


0.2.4 (2017-12-05)
------------------

Added
^^^^^
* Method to lookup the keyword arguments needed for a given path name
* Sphinx plugin to auto document the sdss_access path definitions

.. _changelog-0.2.3:

0.2.3 (2017-12-02)
------------------

Added
^^^^^
* Added new Sphinx documentation and wrote some stuff

Changed
^^^^^^^
* Migrated sdss_access over into the cookiecutter model

