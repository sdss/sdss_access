
.. _intro:

Introduction to sdss_access
===============================

SDSS Access provides a convenient way of navigating local and remote filesystem paths from the Science Archive Server (SAS).
`sdss_access` uses the SDSS Tree product for all path look-ups.

Path Generation
---------------

You can generate full paths to local files easily with `Path.full`::

    # import the path
    from sdss_access import SDSSPath
    path = SDSSPath()

    # generate a file system path
    path.full('mangacube', drpver='v2_3_1', plate='8485', ifu='1901', wave='LOG')
    '/Users/Brian/Work/sdss/sas/mangawork/manga/spectro/redux/v2_3_1/8485/stack/manga-8485-1902-LOGCUBE.fits.gz'

Note that this only generates a path. The file may not actually exist locally.  If you want to generate a URL path to
the file on the SAS at Utah, you can use `Path.url`::

    # generate a http path to the file
    path.url('mangacube', drpver='v2_3_1', plate='8485', ifu='1901', wave='LOG')
    'https://data.sdss.org/sas/mangawork/manga/spectro/redux/v2_3_1/8485/stack/manga-8485-1902-LOGCUBE.fits.gz'

You can also pass in the full path directly as a string in cases.  In those cases, the first argument passed in must
be an empty string.
::

    # pass in the full path directly to path.url
    full = path.full('mangacube', drpver='v2_3_1', plate='8485', ifu='1901', wave='LOG')
    path.url('', full=full)
    'https://data.sdss.org/sas/mangawork/manga/spectro/redux/v2_3_1/8485/stack/manga-8485-1902-LOGCUBE.fits.gz'

Path Names
----------

The syntax for all paths defined in `sdss_access`, for most methods, is ``(name, **kwargs)``.  Each path is defined by
a **name** and several **keyword arguments**, indicated in the template filepath by **{keyword_name}**.  For example,
the path to a MaNGA data cube has **name** ``mangacube`` and path keywords, **plate**, **drpver**, **ifu**, and **wave**,
defined in the path ``$MANGA_SPECTRO_REDUX/{drpver}/{plate}/stack/manga-{plate}-{ifu}-{wave}CUBE.fits.gz``.  All paths
are defined inside the SDSS `tree` product, within a `[PATHS]` section in the environment configuration files, e.g. `data/sdsswork.cfg`
or `data/dr15.cfg`.  Within `sdss_access`, all paths are available as a dictionary, ``path.templates``::

    from sdss_access.path import SDSSPath
    path = SDSSPath()

    # show the dictionary of available paths
    path.templates

To look up what path names are available, you can use ``path.lookup_names``::

    # look up the available path names
    path.lookup_names()
    ['BOSSLyaDR_cat', ..., 'mangacube', ..., 'xdqso_index']

To look up what keywords are needed for a given path, you can use ``path.lookup_keys``::

    # look up the keyword arguments needed to define a MaNGA cube path
    path.lookup_keys('mangacube')
    ['plate', 'drpver', 'ifu', 'wave']

The full list of paths can also be found :ref:`here <paths>`.  To create a new path, see
`Add Paths into the Tree <https://sdss-tree.readthedocs.io/en/latest/paths.html>`_ and follow
the instructions.

To check if a path exists locally, use the ``exists`` method.  To check if the file exists remotely on the SAS, pass in
the ``remote`` keyword argument
::

    # check for local path existence
    path.exists('mangacube', drpver='v2_3_1', plate='8485', ifu='1901', wave='LOG')
    True

    # check for remote path existence on the SAS
    path.exists('mangacube', drpver='v2_3_1', plate='8485', ifu='1901', wave='LOG', remote=True)
    True

Downloading Files
-----------------

You can download files from the SAS and place them in your local SAS.  `sdss_access` expects a local SAS filesystem
that mimics the real SAS at Utah.  If you do not already have a `SAS_BASE_DIR` set, one will be defined in your
home directory, as a new `sas` directory.

sdss_access has four classes designed to facilitate access to SAS data.

- **Access** - class that automatically decides between `RsyncAccess` and `CurlAccess` based on the operating system.
- **HttpAccess** - uses the `urllib` package to download data using a direct http request
- **RsyncAccess** - uses `rsync` to download data.  Available for Linux and MacOS.
- **CurlAccess** - uses `curl` to download data.  This is the only available method for use on Windows machines.

Note that all remote access classes, after instantiation, must call the ``remote()`` method before adding paths to ensure
successful downloading of data.

Using the `HttpAccess` class.

::

    from sdss_access import HttpAccess
    http_access = HttpAccess(verbose=True)

    # set to use remote
    http_access.remote()

    # get the file
    http_access.get('mangacube', drpver='v2_3_1', plate='8485', ifu='1901', wave='LOG')

Using the `RsyncAccess` class.  `RsyncAccess` is generally much faster then `HttpAccess` as it spreads multiple
file downloads across multiple continuous rsync download streams.

::

    # import the rsync class
    from sdss_access import RsyncAccess
    rsync = RsyncAccess()

    # sets a remote mode to the real SAS
    rsync.remote()

    # add all the file(s) you want to download
    # let's download all MPL-6 MaNGA cubes for plate 8485
    rsync.add('mangacube', drpver='v2_3_1', plate='8485', ifu='*', wave='LOG')

    # set the stream tasks
    rsync.set_stream()

    # start the download(s)
    rsync.commit()

The default mode of `RsyncAccess` is for collaboration access.  You can also access data from publicly available
SDSS data releases, by specifying the `public` and `release` keyword arguments on init.

::

    # setup rsync access to download public data from DR14
    rsync = RsyncAccess(public=True, release='dr14')

Using the `CurlAccess` class.  `CurlAccess` behaves exactly the same way as `RsyncAccess`.  After importing and
instantiating a `CurlAccess` object, all methods and behavior are the same as in the `RsyncAccess` class.
::

    # import the curl class
    from sdss_access import CurlAccess
    curl = CurlAccess()

Using the `Access` class.  Depending on your operating system, `posix` or not, Access will either create itself using
`RsyncAccess` or `CurlAccess`, and behave as either object.  Via `Acccess`, Windows machines will always use `CurlAccess`,
while Linux or Macs will automatically utilize `RsyncAccess`.
::

    # import the access class
    from sdss_access import Access
    access = Access()

    # the access mode is automatically set to rsync.
    print(access)
    >>> <Access(access_mode="rsync", using="data.sdss.org")>

    # the class now behaves exactly like RsyncAccess.
    # download a MaNGA cube
    access.remote()
    access.add('mangacube', drpver='v2_3_1', plate='8485', ifu='1901')
    access.set_stream()
    access.commit()

In all all cases, successful `sdss_access` downloads will return a code of 0. Any other number indicates that a problem
occurred.  If no verbose message is displayed, you may need to check the `sdss_access_XX.log` and `sdss_access_XX.err`
files within the temporary directory.

Accessing Public Data Products
------------------------------

The default configuration of all ``sdss_access`` classes, i.e. ``Path``, ``Access``, ``RsyncAccess``, etc. is to use the
``sdsswork`` environment configuration, for access to the most up-to-date filepaths.  To specify paths, or download files, of products from public
data releases, specify the ``release`` keyword and/or the ``public`` keyword.  ``sdss_access`` will automatically set ``public=True`` when the
input release contains ``DRXX``.  You can also explicitly set the ``public`` keyword.
::

    # import the path and set it to use the DR15 release
    from sdss_access.path import Path
    path = Path(release='DR15')

    # check if a public path
    path.public
    True

    # generate a file system path
    path.full('mangacube', drpver='v2_4_3', plate=8485, ifu=1901, wave='LOG')
    '/Users/Brian/Work/sdss/sas/dr15/manga/spectro/redux/v2_4_3/8485/stack/manga-8485-1901-LOGCUBE.fits.gz'

    # setup rsync access to download public data from DR15
    rsync = RsyncAccess(public=True, release='DR15')

.. _sdss-access-svn:

Accessing Paths to Data Files in SVN
------------------------------------

``sdss_access`` can also be used to dynamically build paths to data files contained within SVN software products, e.g.
plugmap files, platelist files, or MaNGA pre-imaging or slitmap files.  To learn how to define these paths, see
`Defining Paths to Data Files in SVN <https://sdss-tree.rtfd.io/en/latest/paths.html#defining-paths-to-data-files-in-svn>`_.

Once the paths are defined, you can access them as usual in ``sdss_access``.  When specifying the full local path,
it uses the local path definition, and for urls, it uses the correct ``svn.sdss.org`` domain.
::

    from sdss_access.path import Path

    # load the paths for sdsswork
    path = Path()
    path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
    '/Users/Brian/Work/sdss/data/manga/mangapreim/trunk/data/D0084XX/8405/preimage-1-42007_irg.jpg'

    path.url('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
    'https://svn.sdss.org/data/manga/mangapreim/trunk/data/D0084XX/tags/8405/preimage-1-42007_irg.jpg'


    # load the paths for DR15
    path = Path(release='DR15')
    path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
    '/Users/Brian/Work/sdss/data/manga/mangapreim/v2_5/data/D0084XX/8405/preimage-1-42007_irg.jpg'

    path.url('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
    'https://svn.sdss.org/public/data/manga/mangapreim/tags/v2_5/data/D0084XX/8405/preimage-1-42007_irg.jpg'

As always, paths generated by ``tree`` and ``sdss_access`` use the directory structure as it exists on the SDSS
Science Archive Server (SAS).  The same is true for paths defined for SVN data files, using the directory structure
as hosted on ``svn.sdss.org`` or products installed with `sdss_install <https://sdss-install.readthedocs.io/en/latest/>`_.
Sometimes this may conflict with locally installed and managed products.  For example, the ``trunk`` version of
the ``mangapreim`` SVN data product is installed locally.
::

    module avail mangapreim

    ----------------------------------------------------------- /Users/Brian/Work/sdss/data/modulefiles ------------------------------------------------------------
    mangapreim/trunk(default)

However, the DR15 generated ``mangapreimg`` path will be the offical tag of the product for DR15, ``v2_5``, which does not
exist locally.  You can always override the generated path to use your local module environment by setting
the ``force_module`` keyword.
::

    # load the paths for DR15
    path = Path(release='DR15')
    path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
    '/Users/Brian/Work/sdss/data/manga/mangapreim/v2_5/data/D0084XX/8405/preimage-1-42007_irg.jpg'

    # Override the path to use my local module
    path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007', force_module=True)
    '/Users/Brian/Work/sdss/data/manga/mangapreim/trunk/data/D0084XX/8405/preimage-1-42007_irg.jpg'

If you want to always override paths with any local modules found, you can set the ``force_modules`` keyword on ``Path``
instantiation.
::

    path = Path(release='DR15', force_modules=True)
    path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
    '/Users/Brian/Work/sdss/data/manga/mangapreim/trunk/data/D0084XX/8405/preimage-1-42007_irg.jpg'

You can also set the ``force_modules`` parameter in your custom config file, ``~/.config/sdss_access/sdss_access.yml`` to
set it once permanently.

.. _sdss-access-windows:

Notes for Windows Users
-----------------------

`sdss_access` downloads files into a directory defined by the `SAS_BASE_DIR` enviroment variable.  If this path points
to another drive other than the C drive, make sure that the new drive and paths have full write permissions available
to `curl`.  `CurlAccess` may not work properly until correct permissions are set up in your folder system.

.. _sdss-access-api:

Reference/API
-------------

.. rubric:: Class

.. autosummary:: sdss_access.path.Path
.. autosummary:: sdss_access.Access
.. autosummary:: sdss_access.HttpAccess
.. autosummary:: sdss_access.RsyncAccess
.. autosummary:: sdss_access.CurlAccess

.. rubric:: Methods

.. autosummary::

    sdss_access.SDSSPath.full
    sdss_access.SDSSPath.url
    sdss_access.SDSSPath.lookup_names
    sdss_access.SDSSPath.lookup_keys
    sdss_access.SDSSPath.extract
    sdss_access.SDSSPath.location
    sdss_access.SDSSPath.name
    sdss_access.SDSSPath.dir
    sdss_access.SDSSPath.any
    sdss_access.SDSSPath.expand
    sdss_access.SDSSPath.random
    sdss_access.SDSSPath.one
    sdss_access.Access.remote
    sdss_access.Access.add
    sdss_access.Access.set_stream
    sdss_access.Access.commit
