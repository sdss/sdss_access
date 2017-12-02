SDSS Python template and coding standards
=========================================

**Important: this is a pre-alpha version of this document. Please, look
throughout the text and at the end of the document for a list of
TODO/missing parts.**

So you want to write some Python code. Congratulations, you've gotten to
the right place! This repository has a dual purpose: it provides a
template for a basic, but complete, Python package; and lists the coding
standards and recommendations for developing code for SDSS. Please, read
this document carefully. If you decide to develop your product based on
this template, feel free to replace the ``README.md`` with a description
of your project, but keep the ``STYLE.md`` file as a reminder of the
coding conventions.

While this document deals with Python product, and some of the solutions
and services suggested are specific for it, much of what is written here
is general good advice for developing software in any platform.

Table of Contents
-----------------

-  `Python 2 vs Python 3: which one to
   choose? <#python-2-vs-python-3-which-one-to-choose>`__
-  `Code storage and ownership. <#code-storage-and-ownership>`__
-  `Versioning and change logs. <#versioning-and-change-logs>`__
-  `Deployment <#deployment>`__
-  `Coding style <#coding-style>`__

   -  `Docstrings <#docstrings>`__
   -  `Linters <#linters>`__
   -  `General advice <#general-advice>`__

-  `Testing <#testing>`__

   -  `Unit testing <#unit-testing>`__
   -  `Continuous integration and
      coverage <#continuous-integration-and-coverage>`__

-  `Automatic documentation
   generation <#automatic-documentation-generation>`__

   -  `Read the Docs <#read-the-docs>`__

-  `Git workflow <#git-workflow>`__
-  `Software Citation <#software-citation>`__

   - `Zenodo <#zenodo>`__
   - `Astrophysical Source Code Library <#ascl>`__

-  `TODO / Questions <#todo--questions>`__

Python 2 vs Python 3: which one to choose?
------------------------------------------

SDSS has made the decision to transition to Python 3 by 2020. That means
that all new code must *at least* be compatible with Python 3. There is,
however, a very significant amount of ancillary code that is still
Python 2-only and that will not be ported to Python 3 for some time.

When deciding what version of Python to write your code on, consider
which are its dependencies:

-  If your code is standalone, or depends on Python 3-compatible code,
   write it in Python 3. **You don't need to make sure your code is
   Python 2-backwards compatible.**

-  If your code depends on key packages that are Python 2-only (e.g.,
   ``actorcore``, ``opscore``, ``RO``, ``twistedActor``), write your
   code in Python 2 **but** try to make it as much Python 3-ready as
   possible, so that when those dependencies are upgraded you can
   upgrade your code easily.

Whenever you create a new Python file, make sure to add the following
lines at the top of the file

.. code:: python

    from __future__ import division
    from __future__ import print_function
    from __future__ import absolute_import

That will force you to use ``import``, ``print``, and division in a way
that is Python 2 and 3-compatible.

Some resources that can be useful to write code that is Python 2 and
3-compatible, and to port code from 2 to 3:

-  A `cheat sheet <http://python-future.org/compatible_idioms.html>`__
   with advice to write code compatible with Python 2 and 3.
-  The `six <https://pythonhosted.org/six/#>`__ library provides
   functions to write code that will work in Python 2 and 3.
-  When converting code from Python 2 to 3, consider using
   `2to3 <https://docs.python.org/2/library/2to3.html>`__ as the
   starting point. It works very well for most files, and even for those
   files that require manual interaction, it paves most of the way.

Code storage and ownership
--------------------------

All code must be version controlled using
`git <https://git-scm.com/>`__. Older code, still under the SVN
repository, can be maintained using Subversion until it has been ported
to Git.

All code must live in the `SDSS GitHub
organisation <https://www.github.com/sdss>`__. When starting a new
product, start a new repository in the GitHub organisation (you can
choose to make it public or private) and follow the instructions to
clone it to your computer. Feel free to create forks of the repositories
to your own GitHub account, but make sure the production version of the
code lives in the organisation repo.

All code must have *at least* one owner, who is ultimately responsible
for keeping the code working and making editorial decisions. Owners can
make decision on which code standards to follow (within the requirements
listed in this document), such as maximum line length, linter, or
testing framework. The owner(s) names should be obvious in the README of
the repo and in the ``setup.py`` file.

Versioning and change logs
--------------------------

Software versions should follow the convention ``X.Y.Z`` (e.g.,
``1.2.5``) where X indicates the major version (large, maybe
non-backwards compatible changes), Y is for minor changes and additions
(backwards compatible), and Z is for bug fixes (no added functionality).
Suffixes to the version, such as ``dev``, ``alpha``, ``beta``, are
accepted. Do not use a hyphen between version and suffix (``1.2.5dev``
is ok, ``1.2.5-dev`` is not).

Version tracking may be complicated so we recommend using
``bumpversion`` (see `here <https://github.com/peritus/bumpversion>`__
for documentation). This template already implements a `configuration
file <./.bumpversion.cfg>`__ that automates updating the version number
in all the places in the code where it appears. Let's say that your
current version is ``0.5.1`` and you are going to work on minor changes
to the product. You can go to the root of the package and run
``bumpversion minor``. This will update the version to ``0.6.0dev``
everywhere needed, and will commit the changes. When you are ready to
release, you can do ``bumpversion release`` to change the version to
``0.6.0``.

All changes should be logged in a ``CHANGELOG.rst`` or ``CHANGELOG.md``
file. See `the template CHANGELOG.rst <./CHANGELOG.rst>`__ for an
example of formatting. When releasing a new version, copy the change log
for the relevant version in the GitHub release description.

Deployment
----------

SDSS Python packages should follow the general Python standards for
packaging. If looking for documentation, `start
here <https://packaging.python.org/>`__.

All packages must contains a `setup.py <./setup.py>`__ to automate
building, installation, and packaging. The ``setup.py`` file must take
care of compiling and linking all external code (e.g., C libraries) that
is used by the project.

Dependencies must be maintained in two different locations. For
standard, pip-installable dependencies, use the
`requirements.txt <./requirements.txt>`__ file. See
`here <https://pip.pypa.io/en/stable/user_guide/#requirements-files>`__
for more information on using requirements.txt files. Consider using
multiple requirements.txt files (e.g, ``requirements.txt``,
``requirements_dev.txt``, ``requirements_docs.txt``) for different
pieces of functionality. Additionally, you must maintain the
`module <etc/python_template.module>`__ file for your product. If you
package depends on SDSS-specific, non pip-installable packages, use the
module file to load the necessary dependencies.

Should you make your package pip-installable? The general answers is
yes, but consider the scope of your project. If your code is to be used
for mountain operations and needs to be maintained with modules/EUPS
version control, making it pip installable may not be necessary, since
it is unlikely to be installed in that way. However, if your product
will be distributed and installed widely in the collaboration (examples
of this include analysis tools, pipelines, schedulers), you *must* make
it pip-installable. Start `here <https://pip.pypa.io/en/stable/>`__ for
some documentation on making pip-installable packages. Another good
resource is `twine <https://github.com/pypa/twine>`__, which will help
you automate much of the packaging and uploading process.

SDSS has a `PyPI account <https://pypi.org/user/sdss/>`__ that should be
used to host released version of your pip-installable projects. Do not
deploy the project in your own account. Instead, contact
`XXX <mailto:me@email.com>`__ to get access to the PyPI account.

Coding style
------------

SDSS code follows the `PEP8
standard <https://www.python.org/dev/peps/pep-0008/>`__. Please, read
that document carefully and follow every convention, unless there are
very good reasons not to.

The only point in which SDSS slightly diverges from PEP8 is the line
length. While the suggested PEP8 maximum line length of 79 characters is
recommended, lines **up to** 99 characters are accepted. When deciding
what line length to use, follow this rule: if you are modifying code
that is not nominally owned by you, respect the line length employed by
the owner of the product; if you are creating a new product that you
will own, feel free to decide your line length, as long as it has fewer
than 99 characters.

It is beyond the scope of this document to summarise the PEP8
conventions, but here are some of the most salient points:

-  Indentation of four spaces. **No tabs. Ever.**
-  Two blank lines between functions and classes. One blank line between
   methods in a class. A single line at the end of each file.
-  Always use spaces around operators and assignments (``a = 1``). The
   only exception is for function and method keyword arguments
   (``my_function(1, key='a')``).
-  No trailing spaces. You can configure your editor to strip the lines
   automatically for you.
-  Imports go on the top of the file. Do **not** import more than one
   package in the same line (``import os, sys``). Maintain the
   namespace, do **not** import all functions in a package
   (``from os import *``). You can import multiple functions from the
   same package at the same time
   (``from os.path import dirname, basename``).
-  Use single quotes for strings. Double quotes must be reserved for
   docstrings and string blocks.
-  For inline comments, at least two spaces between the statement and
   the beginning of the comment
   (``a = 1­­  # This is a comment about a``).
-  Class names must be in camelcase (``class MyClass``). Function,
   method, and variable names should be all lowercase separated by
   underscores for legibility (``def a_function_that_does_something``,
   ``my_variable = 1``). For the latter ones, PEP8 allows some
   flexibility. The general rule of thumb is to make your function,
   method, and variable names descriptive and readable (avoid multiple
   words in all lowercase). As such, if you prefer to use camelcase
   (``aFunctionThatDoesSomething``, ``myVariable = 1``) for your project
   that is accepted, as long as you are consistent throughout the
   project. When modifying somebody else's code, stick to their naming
   decisions.
-  Use ``is`` for comparisons with ``None``, ``True``, or ``False``:
   ``if foo is not None:``.

Docstrings
~~~~~~~~~~

Docstrings are special comments, wrapped between two sets of three
double quotes (``"""``). Their purpose is dual: on one side they provide
clear, well structured documentation for each class and function in your
code. But they are also intended to be read by an automatic
documentation generator (see the `Automatic documentation
generation <#automatic-documentation-generation>`__ section). For
docstrings, follow
`PEP257 <https://www.python.org/dev/peps/pep-0257/>`__. In our template,
`main.py <./python/python_template/main.py>`__ contains some examples of
functions and classes with docstrings; use those as an example. In
general:

-  **All** code should be commented. **All** functions, classes, and
   methods should have a docstring.
-  Use double quotes for docstrings; reserve single quotes for normal
   strings.
-  Limit your docstrings lines to the same line length you are using for
   your code. **TODO: actually PEP237 recommends to use 72 characters.
   Do we follow that?**
-  A complete docstring should start with a single line describing the
   general purpose of the function or class. Then a blank line and and
   in-depth description of the function or class in one or more
   paragraphs. A list of the input parameters (arguments and keywords)
   follows, and a description of the values returned, if any. If the
   class or function merits it, you should include an example of use.
-  The docstring for the ``__init__()`` method in a class goes just
   after the declaration of the class and it explains the general use
   for the class, in addition to the list of parameters accepted by
   ``__init__()``.
-  Private methods and functions (those that start with an underscore)
   may not have a docstring **only** if their purpose is really obvious.
-  In general, we prefer `Google
   style <http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html#example-google>`__
   docstrings over `Numpy
   style <http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html#example-numpy>`__
   ones, but you are free to choose one as long as you stick with it
   across all the product. Avoid styles such as
   ``param path: The path of the file to wrap`` which are difficult to
   read.

Linters
~~~~~~~

Do use a linter. These are plugins available for almost every editor
(vim, emacs, Sublime Text, Atom) that are executed every time you save
your code and show you syntax errors and where you are not following
PEP8 conventions. They normally rely on an underlying library, usually
`pylint <https://www.pylint.org/>`__ or
`flake8 <http://flake8.pycqa.org/en/latest/>`__. This template includes
customised configuration files for both libraries. You can also place
``.flake8`` and ``.pylintrc`` files in your home directory and they will
be used for all your projects (configuration files *in* the root of the
project override the general configuration for that project).

While ``pylint`` is a more fully fleshed library, and provides estimates
on code complexity, docstring linting, etc., it may be a bit excessive
and verbose for most users. ``flake8`` provides more limited features,
but its default configuration is usually what you want (and we enforce
in SDSS). It is up to you to test them and decide which one to use.

Do update the ``.flake8`` or ``.pylintrc`` files in your project with
the specific configuration you want to use in for that product. That is
critical for other people to contribute to the code while keeping your
coding style choices.

File headers
~~~~~~~~~~~~

Include a header in each Python file describing the author, license,
etc. We suggest

.. code:: python

    #!/usr/bin/env python
    # encoding: utf-8
    #
    # @Author:
    # @Date:
    # @Filename:
    # @License:
    # @Copyright:


    from __future__ import division
    from __future__ import print_function
    from __future__ import absolute_import

In general, do not include comments about when you last modified the
file. Instead, use the `changelog <./CHANGELOG.rst>`__ and atomic git
commits.

General advice
~~~~~~~~~~~~~~

-  Blank lines take only one byte; there is no reason for you not to use
   them frequently and improve legibility.
-  Remember the `Zen of
   Python <https://www.python.org/dev/peps/pep-0020/>`__. Explicit is
   better than implicit. Simple is better than complex.

Testing
-------

Do test your code. Do test your code. Do test your code. As repository
owner, you are the ultimate responsible for making sure your code does
what it is supposed to do, and to avoid that new features break current
functionality.

Modern testing standards are based on two cornerstone ideas: `unit
testing <https://en.wikipedia.org/wiki/Unit_testing>`__, and `continuous
integration <https://en.wikipedia.org/wiki/Continuous_integration>`__
(CI).

Unit testing
~~~~~~~~~~~~

Unit testing advocates for breaking your code into small "units" that
you can write tests for (and then actually write the tests!) There are
multiple tutorials and manuals online, `this
one <http://docs.python-guide.org/en/latest/writing/tests/>`__ is a good
starting point.

Many libraries and frameworks for testing exist for Python. The basic
(but powerful) one is called
`unittest <https://docs.python.org/3/library/unittest.html>`__ and is a
standard Python library.
`nose2 <http://nose2.readthedocs.io/en/latest/>`__ provides additional
features, and a nicer interface.
`pytest <https://docs.pytest.org/en/latest/>`__ includes all those extra
features plus a number of extremely convenient and powerful features, as
well as many third-party addons. On the other hand, its learning curve
may be a bit steep.

So, what library should you use? If your code and testing needs are very
simple, ``unittest`` is a good option.

For larger projects, SDSS recommends using ``pytest``. Features such as
`parametrising
tests <https://docs.pytest.org/en/latest/parametrize.html#pytest-mark-parametrize-parametrizing-test-functions>`__
and `fixtures <https://docs.pytest.org/en/latest/fixture.html>`__ are
excellent to make sure your code gets a wide test coverage. This
template includes a simple `pytest
setup <./python/python_template/test>`__. You can also look at the
`Marvin test
suite <https://github.com/sdss/marvin/tree/master/python/marvin/tests>`__
for a more complete example.

Continuous integration and coverage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is critical that you not only write test but run them, and do so in a
suite of environments (different OS, Python versions, etc). Doing that
in your local computer can be convoluted, so we recommend the use of
`Travis CI <https://travis-ci.org/>`__. Travis gets integrated with a
GitHub repository and is triggered every time you commit, make a pull
request, or create a branch. On trigger, you can configure what happens
before the tests are run (e.g, download files, create a database), and
the platforms they run on. For an example of a full Travis setup see the
`Marvin travis
configuration <https://github.com/sdss/marvin/blob/master/.travis.yml>`__.

In addition to running tests, you will want to keep an eye on test
coverage, i.e., what percentage of your code gets "activated" and tested
with your unit tests. Increasing your test coverage should always be a
goal, as it is to make sure that any new feature or bug fix gets
associated tests. You can check your coverage using
`pytest-cov <https://pypi.python.org/pypi/pytest-cov>`__.
`Coveralls <https://coveralls.io/>`__ is another CI service that can be
configured to run after Travis and that provides a nice HTML display of
your coverage and missing lines.

Automatic documentation generation
----------------------------------

As a software developer, it is part of your responsibility to document
your code and keep that documentation up to date. Documentation takes
two forms: inline documentation in the form of comments and docstrings;
and explicit documentation, tutorials, plain-text explanations, etc.

Explicit documentation can take many forms (PDFs, wiki pages, plain text
files) but the rule of thumb is that the best place to keep your
documentation is the product itself. That makes sure a user knows where
to look for the documentation, and keeps it under version control.

SDSS uses and **strongly encourages**
`Sphinx <http://www.sphinx-doc.org/en/stable/intro.html>`__ to
automatically generate documentation. Sphinx translates
`reStructuredText <http://docutils.sourceforge.net/rst.html>`__ source
files to HTML (plugins for Latex, HTML, and other are available). It
also automates the process of gathering the docstrings in your code and
generating nicely formatted HTML code.

It is beyond the purpose of this document to explain how to use Sphinx,
but `its
documentation <http://www.sphinx-doc.org/en/stable/contents.html>`__ is
quite good and multiple tutorials exist online. A large ecosystem of
plugins and extensions exist to perform almost any imaginable task. This
template includes a basic but functional `Sphinx
template <./docs/sphinx>`__ that you can build by running ``make html``.

Read the Docs
~~~~~~~~~~~~~

Deploying your Sphinx documentation is critical. SDSS uses `Read the
Docs <https://readthedocs.org>`__ to automatically build and deploy
documentation. Read the Docs can be added as a plugin to your GitHub
repo for continuous integration so that documentation is built on each
commit. SDSS owns a Read the Docs account. Contact
`XXX <mailto:me@email.com>`__ to deploy your documentation there.

Git workflow
------------

Working with Git and GitHub provides a series of extremely useful tools
to write code collaboratively. Atlassian provides a `good
tutorial <https://www.atlassian.com/git/tutorials/syncing>`__ on Git
workflows. While the topic is an extensive one, here is a simplified
version of a typical Git workflow you should follow:

1. `Clone <https://git-scm.com/docs/git-clone>`__ the repository.
2. Create a `branch <https://git-scm.com/docs/git-branch>`__ (usually
   from master) to work on a bug fix or new feature. Develop all your
   work in that branch. Commit frequently and modularly. Add tests.
3. Once your branch is ready and well tested, and your are ready to
   integrate your changes, you have two options:

   1. If you are the owner of the repo and no other people are
      contributing code at the time (or your changes are **very** small
      and non-controversial) you can simple
      `merge <https://git-scm.com/docs/git-merge>`__ the branch back
      into master and push it to the upstream repo.
   2. If several people are collaborating in a project, you *want* to
      create a `pull
      request <https://help.github.com/articles/about-pull-requests/>`__
      for that branch. The change can then be discussed, changes made
      and, when approved, you can merge the pull request.

4. GOTO 2

You may want to consider the possibility of using
`forks <https://help.github.com/articles/fork-a-repo/>`__ if you are
planning on doing a large-scope change to the code.

Software Citation
-----------------

All software should be archived and citable in some way by anyone who uses it.  The AAS now has a
policy for `software citation <http://journals.aas.org/policy/software.html>`_, that SDSS should adopt
for all pieces of code it produces.  This policy should be adopted by internal SDSS collaborators
as well as astronomers outside SDSS using SDSS software.

Zenodo
~~~~~~

Zenodo allows you to generate a unique digital object identifier (DOI) for any piece of software code in a Github
repository.  DOI's are citable snippets, and allow your software code to be identified by tools.  See `Making Your Code Citable <https://guides.github.com/activities/citable-code/>`_ for how to connect your Github repository to Zenodo.  Once your Github repo is connected to Zenodo, every new Github tag or release gets a new DOI from Zenodo.  Zenodo provides a citable formats for mutiple journals as well as export to a Bibtex file.

Astrophysical Source Code Library
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `ASCL <http://ascl.net/>`_ is a registry of open-source astronomy software, indexed by the
`SAO/NASA Astrophysics Data System <http://ads.harvard.edu/>`_ (ADS).  The process for submission
to the ASCL is outlined `here <http://ascl.net/submissions>`_.

Further reading
---------------

-  Python's own `documentation style
   guide <https://docs.python.org/devguide/documenting.html>`__ is a
   good resource to learn to write good documentation.
