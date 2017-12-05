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

    yield '.. list-table:: {0}'.format(name)
    yield _indent(':widths: 20 50 70')
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


class PathDirective(rst.Directive):
    ''' The directive which instructs Sphinx how to format the Tree config documentation '''

    has_content = False
    required_arguments = 1
    option_spec = {
        'prog': directives.unchanged_required,
        'templates': directives.flag,
    }

    def _load_module(self, module_path):
        """Load the module."""

        # __import__ will fail on unicode,
        # so we ensure module path is a string here.
        module_path = str(module_path)

        try:
            module_name, attr_name = module_path.split(':', 1)
        except ValueError:  # noqa
            raise self.error('"{0}" is not of format "module:parser"'.format(module_path))

        try:
            mod = __import__(module_name, globals(), locals(), [attr_name])
        except (Exception, SystemExit) as exc:  # noqa
            err_msg = 'Failed to import "{0}" from "{1}". '.format(attr_name, module_name)
            if isinstance(exc, SystemExit):
                err_msg += 'The module appeared to call sys.exit()'
            else:
                err_msg += 'The following exception was raised:\n{0}'.format(traceback.format_exc())

            raise self.error(err_msg)

        if not hasattr(mod, attr_name):
            raise self.error('Module "{0}" has no attribute "{1}"'.format(module_name, attr_name))

        return getattr(mod, attr_name)

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

        command = self._load_module(self.arguments[0])

        if 'prog' in self.options:
            prog_name = self.options.get('prog')
        else:
            raise self.error(':prog: must be specified')

        # get instance
        path = command()

        # get options
        templates = 'templates' in self.options

        # add a new section for paths
        return self._generate_nodes(prog_name, path, templates=templates)


def setup(app):
    app.add_directive('datamodel', PathDirective)



