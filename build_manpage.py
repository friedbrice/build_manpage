# -*- coding: utf-8 -*-

"""build_manpage command -- Generate man page from argparse/dist metadata.
Nabbed from https://andialbrecht.wordpress.com/2009/03/17/creating-a-man-page-with-distutils-and-optparse/
Altered for argparse
"""

from setuptools import Command, distutils

import argparse
import datetime


class ManPageFormatter(argparse.HelpFormatter):
    def __init__(self):
        pass

    def _markup(self, txt):
        """Prepares txt to be used in man pages."""
        return txt.replace('-', '\\-')

    def format_usage(self, usage):
        """Formate the usage/synopsis line."""
        return self._markup(usage)

    def format_heading(self, heading):
        """Format a heading.
        If level is 0 return an empty string. This usually is the string "Options".
        """
        if self.level == 0:
            return ''
        return '.TP\n%s\n' % self._markup(heading.upper())

    def format_option(self, option):
        """Format a single option.
        The base class takes care to replace custom argparse values.
        """
        result = []
        opts = self.option_strings[option]
        result.append('.TP\n.B %s\n' % self._markup(opts))
        if option.help:
            help_text = '%s\n' % self._markup(self.expand_default(option))
            result.append(help_text)
        return ''.join(result)


class build_manpage(Command):
    description = 'Generate a man page.'
    user_options = [
        ('output=', 'O', 'output file'),
        ('parser=', None, 'module path to parser (e.g. mymod:func'),
        ]

    def _markup(self, txt):
        return txt.replace('-', '\\-')

    def initialize_options(self):
        self.output = None
        self.parser = None
        self.seealso = None
    

    def finalize_options(self):
        if self.output is None:
            raise distutils.errors.DistutilsOptionError('\'output\' option is required')
        if self.parser is None:
            raise distutils.errors.DistutilsOptionError('\'parser\' option is required')
        mod_name, func_name = self.parser.split(':')
        fromlist = mod_name.split('.')
        try:
            mod = __import__(mod_name, fromlist=fromlist)
            self._parser = getattr(mod, func_name)()
        except ImportError as err:
            raise
        self._parser.formatter = ManPageFormatter()
        self.announce('Writing man page %s' % self.output)
        self._today = datetime.date.today()

    def _write_header(self):
        appname = self.distribution.get_name()
        ret = []
        ret.append('.TH %s 1 %s\n' % (self._markup(appname),
                                      self._today.strftime('%Y\\-%m\\-%d')))
        description = self.distribution.get_description()
        if description:
            name = self._markup('%s - %s' % (self._markup(appname),
                                             description.splitlines()[0]))
        else:
            name = self._markup(appname)
        ret.append('.SH NAME\n%s\n' % name)
        synopsis = self._parser.format_usage()
        if synopsis:
            synopsis = synopsis.replace('%s ' % appname, '')
            ret.append('.SH SYNOPSIS\n.B %s\n%s\n' % (self._markup(appname),
                                                      synopsis))
        long_desc = self.distribution.get_long_description()
        if long_desc:
            ret.append('.SH DESCRIPTION\n%s\n' % self._markup(long_desc))
        return ''.join(ret)

    def _write_options(self):
        ret = ['.SH OPTIONS\n']
        ret.append(self._parser.format_help())
        return ''.join(ret)

    def _write_seealso(self):
        ret = []
        if self.seealso is not None:
            ret.append('.SH "SEE ALSO"\n')

            for i in self.seealso:
                name, sect = i.split(":")

                if len(ret) > 1:
                    ret.append(',\n')

                ret.append('.BR %s (%s)' % (name, sect))
        return ''.join(ret)

    def _write_footer(self):
        ret = []
        appname = self.distribution.get_name()
        author = '%s <%s>' % (self.distribution.get_author(),
                              self.distribution.get_author_email())
        ret.append(('.SH AUTHORS\n.B %s\nwas written by %s.\n'
                    % (self._markup(appname), self._markup(author))))
        homepage = self.distribution.get_url()
        ret.append(('.SH DISTRIBUTION\nThe latest version of %s may '
                    'be downloaded from\n'
                    '.UR %s\n.UE\n'
                    % (self._markup(appname), self._markup(homepage),)))
        return ''.join(ret)

    def run(self):
        manpage = []
        manpage.append(self._write_header())
        manpage.append(self._write_options())
        manpage.append(self._write_footer())
        manpage.append(self._write_seealso())
        stream = open(self.output, 'w')
        stream.write(''.join(manpage))
        stream.close()
