#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2021-06-20
# @Filename: noxfile.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import contextlib
import os
import tempfile

import nox


@contextlib.contextmanager
def cd(path):
    CWD = os.getcwd()

    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(CWD)


@nox.session(name="docs-live", reuse_venv=True)
def docs_live(session):
    if session.posargs:
        docs_dir = session.posargs[0]
    else:
        docs_dir = "."

    with cd(os.path.join(os.path.dirname(__file__), "docs/sphinx")):
        with tempfile.TemporaryDirectory() as destination:
            session.run(
                "sphinx-autobuild",
                # for sphinx-autobuild
                "--port=0",
                "--open-browser",
                # for sphinx
                "-b=dirhtml",
                "-a",
                "--watch=../../src",
                docs_dir,
                destination,
                external=True,
            )
