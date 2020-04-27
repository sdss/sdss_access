# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-12-05 10:33:59
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2017-12-05 10:53:56

from __future__ import print_function, division, absolute_import
from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils import statemachine
import traceback
import importlib
import re
from sdss_access.path.changelog import get_available_releases

# This file is a basic example of how to write a Sphinx plugin to document
# custom data.


def _indent(text, level=1):
    ''' Does a proper indenting for Sphinx rst '''

    prefix = ' ' * (4 * level)

    def prefixed_lines():
        for line in text.splitlines(True):
            yield (prefix + line if line.strip() else line)

    return ''.join(prefixed_lines())


def _format_templates(name, command, templates):
    ''' Creates a list-table directive

    for a set of defined environment variables

    Parameters:
        name (str):
            The name of the config section
        command (object):
            The sdss_access path instance
        templates (dict):
            A dictionary of the path templates

    Yields:
        A string rst-formated list-table directive

    '''

    yield '.. list-table:: {0} path definitions'.format(name)
    yield _indent(':widths: 20 100 70')
    yield _indent(':header-rows: 1')
    yield ''
    yield _indent('* - Name')
    yield _indent('  - Template')
    yield _indent('  - Kwargs')
    for key, var in templates.items():
        kwargs = command.lookup_keys(key)
        yield _indent('* - {0}'.format(key))
        yield _indent('  - {0}'.format(var))
        yield _indent('  - {0}'.format(', '.join(kwargs)))
    yield ''


def _format_changelog(changes):
    ''' Format a changelog for a sdss_access Paths '''

    yield '.. role:: maroon'

    # yield lines from the PATHS section

    # list mode
    for line in changes:
        if 'Changes' in line:
            yield f'**{line}**'
            yield ''
        elif 'New' in line or 'Updated' in line:
            yield '* ' + _indent(f'**{line.strip()}**')
        elif re.search('[a-z]', line):
            # nested list From To
            if line.strip().startswith(('from', 'to')):
                line = line.replace('to:', '**To:**').replace('from:', '**From:**')
                yield _indent('    * ' + line, level=2)
            else:
                name, template = line.split(':', 1)
                yield _indent(f'    * :maroon:`{name}`: {template}')


def load_module(module_path, error=None, products=None):
    """Load the module."""

    # Exception to raise
    error = error if error else RuntimeError

    # __import__ will fail on unicode,
    # so we ensure module path is a string here.
    module_path = str(module_path)
    try:
        module_name, attr_name = module_path.split(':', 1)
    except ValueError:  # noqa
        raise error('"{0}" is not of format "module:object"'.format(module_path))

    # import the module
    try:
        mod = importlib.import_module(module_name)
    except (Exception, SystemExit) as exc:
        err_msg = 'Failed to import module "{0}". '.format(module_name)
        if isinstance(exc, SystemExit):
            err_msg += 'The module appeared to call sys.exit()'
        else:
            err_msg += 'The following exception was raised:\n{0}'.format(
                traceback.format_exc())

        raise error(err_msg)

    # check what kind of module
    if products:
        module = mod.dm.products
    else:
        module = mod

    if not hasattr(module, attr_name):
        raise error('Module "{0}" has no attribute "{1}"'.format(module_name, attr_name))

    return getattr(module, attr_name)


class PathDirective(rst.Directive):
    ''' The directive which instructs Sphinx how to format the Tree config documentation '''

    has_content = False
    required_arguments = 1
    option_spec = {
        'prog': directives.unchanged_required,
        'templates': directives.flag,
    }

    def _generate_nodes(self, name, command, templates=None):
        """Generate the relevant Sphinx nodes.

        Generates a section for the Tree datamodel.  Formats a tree section
        as a list-table directive.

        Parameters:
            name (str):
                The name of the config to be documented, e.g. 'sdsswork'
            command (object):
                The loaded module
            templates (bool):
                If True, generate a section for the path templates

        Returns:
            A section docutil node

        """

        # the source name
        source_name = name

        # Title
        section = nodes.section(
            '',
            nodes.title(text=name),
            ids=[nodes.make_id(name)],
            names=[nodes.fully_normalize_name(name)])

        # Summarize
        result = statemachine.ViewList()

        if templates:
            lines = _format_templates(name, command, command.templates)

        for line in lines:
            result.append(line, source_name)

        self.state.nested_parse(result, 0, section)

        return [section]

    def run(self):
        self.env = self.state.document.settings.env

        command = load_module(self.arguments[0])

        if 'prog' in self.options:
            prog_name = self.options.get('prog')
        else:
            raise self.error(':prog: must be specified')

        # get instance
        path = command(release=prog_name, public='DR' in prog_name)

        # get options
        templates = 'templates' in self.options

        # add a new section for paths
        return self._generate_nodes(prog_name, path, templates=templates)


class PathChangeDirective(rst.Directive):
    has_content = False
    required_arguments = 1
    option_spec = {
        'prog': directives.unchanged_required,
        'title': directives.unchanged,
        'drs': directives.unchanged_required,
    }

    def run(self):
        self.env = self.state.document.settings.env

        command = load_module(self.arguments[0])

        if 'prog' in self.options:
            prog_name = self.options.get('prog')
        else:
            raise self.error(':prog: must be specified')

        # get drs
        drs = self.options.get('drs').replace(' ', '')
        if drs == 'latest':
            releases = get_available_releases(public=True)
            old, new = releases[-2:]
        else:
            new, old = drs.split(',')

        # compute and format the changelog lines
        lines = command(new, old, to_list=True)
        title = lines[0]
        lines = lines[1:]
        lines = _format_changelog(lines)

        # the source name
        source_name = title

        # Title
        section = nodes.section(
            '',
            nodes.title(text=source_name),
            ids=[nodes.make_id(source_name)],
            names=[nodes.fully_normalize_name(source_name)])

        result = statemachine.ViewList()
        for line in lines:
            result.append(line, source_name)

        self.state.nested_parse(result, 0, section)

        return [section]


def setup(app):
    app.add_directive('datamodel', PathDirective)
    app.add_directive('changelog', PathChangeDirective)



