# -*- coding: utf-8 -*-
"""
    wakatime.languages
    ~~~~~~~~~~~~~~~~~~

    Parse dependencies from a source code file.

    :copyright: (c) 2014 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""

import logging
import re
import sys
import traceback

from ..compat import u, open, import_module


log = logging.getLogger('WakaTime')


class TokenParser(object):
    """The base class for all dependency parsers. To add support for your
    language, inherit from this class and implement the :meth:`parse` method
    to return a list of dependency strings.
    """
    exclude = []

    def __init__(self, source_file, lexer=None):
        self.tokens = []
        self.dependencies = []
        self.source_file = source_file
        self.lexer = lexer
        self.exclude = [re.compile(x, re.IGNORECASE) for x in self.exclude]

    def parse(self, tokens=[]):
        """ Should return a list of dependencies.
        """
        if not tokens and not self.tokens:
            self.tokens = self._extract_tokens()
        raise Exception('Not yet implemented.')

    def append(self, dep, truncate=False, separator=None, truncate_to=None,
               strip_whitespace=True):
        self._save_dependency(
            dep,
            truncate=truncate,
            truncate_to=truncate_to,
            separator=separator,
            strip_whitespace=strip_whitespace,
        )

    def partial(self, token):
        return u(token).split('.')[-1]

    def _extract_tokens(self):
        if self.lexer:
            try:
                with open(self.source_file, 'r', encoding='utf-8') as fh:
                    return self.lexer.get_tokens_unprocessed(fh.read(512000))
            except:
                pass
            try:
                with open(self.source_file, 'r', encoding=sys.getfilesystemencoding()) as fh:
                    return self.lexer.get_tokens_unprocessed(fh.read(512000))
            except:
                pass
        return []

    def _save_dependency(self, dep, truncate=False, separator=None,
                         truncate_to=None, strip_whitespace=True):
        if truncate:
            if separator is None:
                separator = u('.')
            separator = u(separator)
            dep = dep.split(separator)
            if truncate_to is None or truncate_to < 1:
                truncate_to = 1
            if truncate_to > len(dep):
                truncate_to = len(dep)
            dep = dep[0] if len(dep) == 1 else separator.join(dep[:truncate_to])
        if strip_whitespace:
            dep = dep.strip()
        if dep and (not separator or not dep.startswith(separator)):
            should_exclude = False
            for compiled in self.exclude:
                if compiled.search(dep):
                    should_exclude = True
                    break
            if not should_exclude:
                self.dependencies.append(dep)


class DependencyParser(object):
    source_file = None
    lexer = None
    parser = None

    def __init__(self, source_file, lexer):
        self.source_file = source_file
        self.lexer = lexer

        if self.lexer:
            module_name = self.lexer.__module__.rsplit('.', 1)[-1]
            class_name = self.lexer.__class__.__name__.replace('Lexer', 'Parser', 1)
        else:
            module_name = 'unknown'
            class_name = 'UnknownParser'

        try:
            module = import_module('.%s' % module_name, package=__package__)
            try:
                self.parser = getattr(module, class_name)
            except AttributeError:
                log.debug('Module {0} is missing class {1}'.format(module.__name__, class_name))
        except ImportError:
            log.debug(traceback.format_exc())

    def parse(self):
        if self.parser:
            plugin = self.parser(self.source_file, lexer=self.lexer)
            dependencies = plugin.parse()
            return list(set(dependencies))
        return []
