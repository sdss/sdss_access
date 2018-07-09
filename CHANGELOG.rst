.. _sdss_access-changelog:

==========
Change Log
==========

This document records the main changes to the sdss_access code.

0.2.5 (unreleased)
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

