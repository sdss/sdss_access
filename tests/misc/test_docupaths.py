# !usr/bin/env python
# -*- coding: utf-8 -*-
#

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def rootdir():
    return Path(__file__).resolve().parent.parent / "roots"


@pytest.mark.sphinx(testroot="docupaths")
def test_docupaths(app, status, warning):
    app.builder.build_all()

    dmdoc = app.srcdir / "_build/html/contents.html"
    assert dmdoc.exists()

    tt = dmdoc.read_text()

    # check for datamodel directive stuff
    assert '<section id="datamodel">' in tt
    assert (
        '<h2>DR17<a class="headerlink" href="#dr17" title="Link to '
        + 'this heading">¶</a></h2>'
        in tt
    )
    assert (
        "<td><p>$MANGA_SPECTRO_REDUX/{drpver}/{plate}/stack/manga-{plate}-{ifu}-{wave}CUBE.fits.gz</p></td>"
        in tt
    )

    # check for changelog directive stuff
    assert '<section id="changelog">' in tt
    assert "Changes: DR17 from DR16" in tt
    assert "<dt><strong>New Paths:</strong></dt><dd><ul>" in tt
    assert (
        '<li><p><span class="maroon">apogee_astronn</span>:  '
        + "$APOGEE_ASTRONN/apogee_astroNN-{release}.fits</p></li>"
        in tt
    )
