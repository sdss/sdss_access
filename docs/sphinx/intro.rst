
.. _intro:

Introduction to sdss_access
===============================

SDSS Access provides a convenient way of navigating local and remote filesystem paths from the Science Archive Server (SAS).
``sdss_access`` uses the SDSS Tree product for all path look-ups.

Concept
-------

SDSS Access works with abstract filepaths to data products, as a way of easily generating paths to specific data products.
An abstract filepath is a generalized path that represents the path to the data product or `file_species`, and can be
resolved to an example of any individual file of that "file_species".  A abstract path is defined by:

* **path_name**: a reference name to the data product or `file_species`
* **path_template**: a string filepath starting with an environment variable, and using {} templating for keyword variable replacement

These paths are defined in the tree product as `path_name = path_template`. See
`Defining New Paths <https://sdss-tree.readthedocs.io/en/latest/paths.html>`_ for more info.
For example, the abstract path for the MaNGA cube data products is
::

    # path_name = path_template
    mangacube = '$MANGA_SPECTRO_REDUX/{drpver}/{plate}/stack/manga-{plate}-{ifu}-{wave}CUBE.fits.gz'

The variable names within the `{}` are specified at runtime to create a path to a specific file on disk.


Path Generation
---------------

You can generate full paths to local files easily with `Path.full <.BasePath.full>`.
::

    # import the path
    from sdss_access import Path
    path = Path(release='dr17')

    # generate a file system path
    path.full('mangacube', drpver='v3_1_1', plate='8485', ifu='1901', wave='LOG')
    '/Users/Brian/Work/sdss/sas/dr17/manga/spectro/redux/v3_1_1/8485/stack/manga-8485-1901-LOGCUBE.fits.gz'

Note that this only generates a path. The file may not actually exist locally.  If you want to generate a URL path to
the file on the SAS at Utah, you can use `Path.url <.BasePath.url>`.
::

    # generate a http path to the file
    path.url('mangacube', drpver='v3_1_1', plate='8485', ifu='1901', wave='LOG')
    'https://data.sdss.org/sas/dr17/manga/spectro/redux/v3_1_1/8485/stack/manga-8485-1901-LOGCUBE.fits.gz'

You can also pass in the full path directly as a string in cases.  In those cases, the first argument passed in must
be an empty string.
::

    # pass in the full path directly to path.url
    full = path.full('mangacube', drpver='v3_1_1', plate='8485', ifu='1901', wave='LOG')
    path.url('', full=full)
    'https://data.sdss.org/sas/dr17/manga/spectro/redux/v3_1_1/8485/stack/manga-8485-1901-LOGCUBE.fits.gz'

Path Names
----------

The syntax for all paths defined in ``sdss_access``, for most methods, is ``(name, **kwargs)``.  Each path is defined by
a **name** and several **keyword arguments**, indicated in the template filepath by **{keyword_name}**.  For example,
the path to a MaNGA data cube has **name** ``mangacube`` and path keywords, **plate**, **drpver**, **ifu**, and **wave**,
defined in the path ``$MANGA_SPECTRO_REDUX/{drpver}/{plate}/stack/manga-{plate}-{ifu}-{wave}CUBE.fits.gz``.  All paths
are defined inside the SDSS ``tree`` product, within a `[PATHS]` section in the environment configuration files, e.g. `data/sdsswork.cfg`
or `data/dr15.cfg`.  Within ``sdss_access``, all paths are available as a dictionary, ``path.templates``::

    from sdss_access.path import Path
    path = Path(release='dr17')

    # show the dictionary of available paths
    path.templates

To look up what path names are available, you can use `Path.lookup_names <.BasePath.lookup_names>`.
::

    # look up the available path names
    path.lookup_names()
    ['BOSSLyaDR_cat', ..., 'mangacube', ..., 'xdqso_index']

To look up what keywords are needed for a given path, you can use `Path.lookup_keys <.BasePath.lookup_keys>`.
::

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
    path.exists('mangacube', drpver='v3_1_1', plate='8485', ifu='1901', wave='LOG')
    True

    # check for remote path existence on the SAS
    path.exists('mangacube', drpver='v3_1_1', plate='8485', ifu='1901', wave='LOG', remote=True)
    True

Required Keywords
-----------------

All the keyword variables defined in a **path_template**, and returned by `Path.lookup_keys <.BasePath.lookup_keys>`,
are required.  Not specifying all the keywords will result in an error raised.

::

    >>> path = Path(release='dr17')

    >>> # see the required keys
    >>> path.lookup_keys('mangacube')
    ['plate', 'drpver', 'wave', 'ifu']

    >>> path.full('mangacube', drpver='v3_1_1', plate='8485', ifu='1901')
    KeyError: "Missing required keyword arguments: ['wave']"

Environment Paths
-----------------

By default, when instantiating a new `.Path`, it will automatically load the ``tree`` environment from any currently loaded
module file, identified with any `TREE_VER` environment variable.  Otherwise it loads the ``sdsswork`` environment, and all
paths relevant to that environment.
::

    >>> # load the default environment / paths
    >>> from sdss_access.path import Path
    >>> path = Path()
    >>> path
    <Path(release="sdsswork", public=False, n_paths=233)

To access paths from a different environment, you can change environments by passing in the ``release`` keyword argument.  The
``release`` acts as an indicator for both a valid data release, e.g. "DR15", and a valid environment configuration,
e.g. "sdsswork".
::

    >>> # load the SDSS-V environment and paths
    >>> from sdss_access.path import Path
    >>> path = Path(release='sdsswork')
    >>> path
    <Path(release="sdsswork", public=False, n_paths=233)

    >>> # switch to the environment for public data release DR17
    >>> path = Path(release='DR17')
    >>> path
    <Path(release="dr17", public=True, n_paths=420)

When reloading a new ``tree`` environment configuration, ``sdss_access`` automatically updates the Python session
``os.environ`` with the relevant environment variables for the given release/configuration.  You can preserve your original
``os.environ`` by setting the ``preserve_envvars`` keyword to True. This will preserve your original environment in its
entirety.
::

    >>> # load the SDSS-V environment but preserve your original os.environ
    >>> path = Path(release='sdsswork', preserve_envvars=True)

Alternatively, you can preserve a subset of enviroment variables from your original ``os.environ`` by passing in a list of
environment variables.
::

    >>> # preserve only a single environment variable
    >>> path = Path(release='sdsswork', preserve_envvars=['ROBOSTRATEGY_DATA'])

If you wish to permanently preserve your locally set environment variables, you can set the ``preserve_envvars`` parameter to
``true`` in a custom tree YAML configuration file located at ``~/.config/sdss/sdss_access.yml``.  For example
::

    preserve_envvars: true

Alternatively, you can permanently set a subset of environment variables to preserve by defining a list.
::

    preserve_envvars:
      - ROBOSTRATEGY_DATA
      - ALLWISE_DIR

Extracting Keywords from Filepaths
----------------------------------

You can extract the keyword variables from a specific filepath, by using the `Path.extract <.BasePath.extract>` method
and specifying the **path_name** reference, and the full filepath.  For the extraction to work, the path to the file
must match the SAS directory structure, and have the relevant environment variable defined from the **path_template**.
::

    >>> # set a path to a file
    >>> filepath = '/Users/Brian/Work/sdss/sas/dr17/manga/spectro/redux/v3_1_1/8485/stack/manga-8485-1901-LOGCUBE.fits.gz'

    >>> # extract the keywords
    >>> path = Path(release='dr17')
    >>> path.extract('mangacube', filepath)
    {'drpver': 'v3_1_1', 'plate': '8485', 'ifu': '1901', 'wave': 'LOG'}


Downloading Files
-----------------

You can download files from the SAS and place them in your local SAS.  ``sdss_access`` expects a local SAS filesystem
that mimics the real SAS at Utah.  If you do not already have a `SAS_BASE_DIR` set, one will be defined in your
home directory, as a new ``sas`` directory.

``sdss_access`` requires valid authentication to download proprietary data.  See :ref:`auth`
for more information.

sdss_access has four classes designed to facilitate access to SAS data.

- **Access** - class that automatically decides between `.RsyncAccess` and `.CurlAccess` based on the operating system.
- **HttpAccess** - uses the `urllib` package to download data using a direct http request
- **RsyncAccess** - uses `rsync` to download data.  Available for Linux and MacOS.
- **CurlAccess** - uses `curl` to download data.  This is the only available method for use on Windows machines.

Note that all remote access classes, after instantiation, must call the `Access.remote <.BaseAccess.remote>` method before
adding paths to ensure successful downloading of data.

Using the `.HttpAccess` class.

::

    from sdss_access import HttpAccess
    http_access = HttpAccess(release='DR17', verbose=True)

    # set to use remote
    http_access.remote()

    # get the file
    http_access.get('mangacube', drpver='v3_1_1', plate='8485', ifu='1901', wave='LOG')

Using the `.RsyncAccess` class.  `.RsyncAccess` is generally much faster then `.HttpAccess` as it spreads multiple
file downloads across multiple continuous rsync download streams.

::

    # import the rsync class
    from sdss_access import RsyncAccess
    rsync = RsyncAccess(release='DR17')

    # sets a remote mode to the real SAS
    rsync.remote()

    # add all the file(s) you want to download
    # let's download all DR17 MaNGA cubes for plate 8485
    rsync.add('mangacube', drpver='v3_1_1', plate='8485', ifu='*', wave='LOG')

    # set the stream tasks
    rsync.set_stream()

    # start the download(s)
    rsync.commit()

Using the `.CurlAccess` class.  `.CurlAccess` behaves exactly the same way as `.RsyncAccess`.  After importing and
instantiating a `.CurlAccess` object, all methods and behavior are the same as in the `.RsyncAccess` class.
::

    # import the curl class
    from sdss_access import CurlAccess
    curl = CurlAccess(release='DR17')

Using the `.Access` class.  Depending on your operating system, ``posix`` or not, Access will either create itself using
`.RsyncAccess` or `.CurlAccess`, and behave as either object.  Via `.Acccess`, Windows machines will always use `.CurlAccess`,
while Linux or Macs will automatically utilize `.RsyncAccess`.
::

    # import the access class
    from sdss_access import Access
    access = Access(release='DR17')

    # the access mode is automatically set to rsync.
    print(access)
    >>> <Access(access_mode="rsync", using="data.sdss.org")>

    # the class now behaves exactly like RsyncAccess.
    # download a MaNGA cube
    access.remote()
    access.add('mangacube', drpver='v3_1_1', plate='8485', ifu='1901')
    access.set_stream()
    access.commit()

In all all cases, successful ``sdss_access`` downloads will return a code of 0. Any other number indicates that a problem
occurred.  If no verbose message is displayed, you may need to check the ``sdss_access_XX.log`` and ``sdss_access_XX.err``
files within the temporary directory.

Downloading with Resolved Paths
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you already have a list of resolved filepaths or urls that you wish to use ``sdss_access``
to download, you can add them using the ``.add_file`` method, instead of the ``.add`` method.
The ``.add`` method takes as input a ``path_name`` and set of path template keyword
arguments, while ``.add_file`` takes either a fully resolved url, filepath, or location.
The ``input_type`` keyword specifies the type of path input.
::

    from sdss_access import RsyncAccess
    rsync = RsyncAccess(release='DR17')
    rsync.remote()

    # add a url to the stream for download
    url = 'rsync://dtn.sdss.org/dr17/manga/spectro/redux/v3_1_1/8485/stack/manga-8485-1901-LOGCUBE.fits.gz'
    rsync.add_file(f, input_type='url')

    # add a file to the stream for download
    path = '/Users/Brian/Work/sdss/sas/dr17/manga/spectro/redux/v3_1_1/8485/stack/manga-8485-1902-LOGCUBE.fits.gz'
    rsync.add_file(path, input_type='filepath')


Accessing SDSS-V Products
-------------------------

With SDSS-V, the usage of ``sdss_access`` remains the same.  The only difference is SDSS-V
products are now delivered by the "data.sdss5.org" server instead of "data.sdss.org".
When specifying ``release="sdss5"``, you may notice the new server location, e.g.
::

    >>> from sdss_access import Access
    >>> access = Access()
    >>> access
    <Access(access_mode="rsync", using="data.sdss5.org")>

As with SDSS-IV, ``sdss_access`` requires valid authentication to download
proprietary data for SDSS-V.  See :ref:`auth` for more information.  Here is an example accessing
the robostrategy completeness files for SDSS-V.

.. warning::
    The below example contains large data, ~8 GB, and may take a while to download.

::

    from sdss_access import Access
    access = Access()
    access.remote()
    access.add('rsCompleteness', observatory='apo', plan='epsilon-2-core-*')
    access.set_stream()
    access.commit()

.. note::
    As of ``version >= 3.0.0``, and ``tree >= 4.0.0`` the default config of "sdsswork" is for SDSS-V
    data products.  In ``versions >2.0 - <3.0``, the "sdsswork" config is for SDSS-V data products, and SDSS-V
    data products can be accessed using the "sdss5" config or release name.

Accessing Public Data Products
------------------------------

The default configuration of all ``sdss_access`` classes, i.e. ``Path``, ``Access``, ``RsyncAccess``, etc. is to use the
``sdsswork`` environment configuration, for access to proprietary data or up-to-date filepaths.  To specify paths,
or download files, of products from public data releases, specify the ``release`` keyword.  ``sdss_access`` will
automatically set ``public=True`` when the input release contains ``DRXX``.  You can also explicitly set
the ``public`` keyword.
::

    # import the path and set it to use the DR17 release
    from sdss_access.path import Path
    path = Path(release='DR17')

    # check if a public path
    path.public
    True

    # generate a file system path
    path.full('mangacube', drpver='v3_1_1', plate=8485, ifu=1901, wave='LOG')
    '/Users/Brian/Work/sdss/sas/dr17/manga/spectro/redux/v3_1_1/8485/stack/manga-8485-1901-LOGCUBE.fits.gz'

    # setup rsync access to download public data from DR17
    rsync = RsyncAccess(public=True, release='DR17')

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

    # load the paths for DR17
    path = Path(release='DR17')
    path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
    '/Users/Brian/Work/sdss/data/manga/mangapreim/v2_9/data/D0084XX/8405/preimage-1-42007_irg.jpg'

    path.url('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
    'https://svn.sdss.org/public/data/manga/mangapreim/tags/v2_9/data/D0084XX/8405/preimage-1-42007_irg.jpg'

As always, paths generated by ``tree`` and ``sdss_access`` use the directory structure as it exists on the SDSS
Science Archive Server (SAS).  The same is true for paths defined for SVN data files, using the directory structure
as hosted on ``svn.sdss.org`` or products installed with `sdss_install <https://sdss-install.readthedocs.io/en/latest/>`_.
Sometimes this may conflict with locally installed and managed products.  For example, the ``trunk`` version of
the ``mangapreim`` SVN data product is installed locally.
::

    module avail mangapreim

    ----------------------------------------------------------- /Users/Brian/Work/sdss/data/modulefiles ------------------------------------------------------------
    mangapreim/trunk(default)

However, the DR17 generated ``mangapreimg`` path will be the offical tag of the product for DR17, ``v2_9``, which does not
exist locally.  You can always override the generated path to use your local module environment by setting
the ``force_module`` keyword.
::

    # load the paths for DR17
    path = Path(release='DR17')
    path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
    '/Users/Brian/Work/sdss/data/manga/mangapreim/v2_9/data/D0084XX/8405/preimage-1-42007_irg.jpg'

    # Override the path to use my local module
    path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007', force_module=True)
    '/Users/Brian/Work/sdss/data/manga/mangapreim/trunk/data/D0084XX/8405/preimage-1-42007_irg.jpg'

If you want to always override paths with any local modules found, you can set the ``force_modules`` keyword on ``Path``
instantiation.
::

    path = Path(release='DR17', force_modules=True)
    path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
    '/Users/Brian/Work/sdss/data/manga/mangapreim/trunk/data/D0084XX/8405/preimage-1-42007_irg.jpg'

You can also set the ``force_modules`` parameter in your custom config file, ``~/.config/sdss/sdss_access.yml`` to
set it once permanently.

.. _sdss-access-windows:

Notes for Windows Users
-----------------------

``sdss_access`` downloads files into a directory defined by the `SAS_BASE_DIR` enviroment variable.  If this path points
to another drive other than the C drive, make sure that the new drive and paths have full write permissions available
to `curl`.  `.CurlAccess` may not work properly until correct permissions are set up in your folder system.

.. _sdss-access-api:

Reference/API
-------------

.. rubric:: Class

.. autosummary:: sdss_access.path.path.Path
.. autosummary:: sdss_access.sync.access.Access
.. autosummary:: sdss_access.sync.http.HttpAccess
.. autosummary:: sdss_access.sync.rsync.RsyncAccess
.. autosummary:: sdss_access.sync.curl.CurlAccess

.. rubric:: Methods

.. autosummary::

    sdss_access.path.path.BasePath.full
    sdss_access.path.path.BasePath.url
    sdss_access.path.path.BasePath.lookup_names
    sdss_access.path.path.BasePath.lookup_keys
    sdss_access.path.path.BasePath.extract
    sdss_access.path.path.BasePath.location
    sdss_access.path.path.BasePath.name
    sdss_access.path.path.BasePath.dir
    sdss_access.path.path.BasePath.any
    sdss_access.path.path.BasePath.expand
    sdss_access.path.path.BasePath.random
    sdss_access.path.path.BasePath.one
    sdss_access.sync.baseaccess.BaseAccess.remote
    sdss_access.sync.baseaccess.BaseAccess.add
    sdss_access.sync.baseaccess.BaseAccess.set_stream
    sdss_access.sync.baseaccess.BaseAccess.commit
