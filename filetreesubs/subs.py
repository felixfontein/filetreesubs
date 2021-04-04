# -*- coding: utf-8 -*-

# Copyright © 2014—2017 Felix Fontein.
#
# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""The main substitution code"""

from __future__ import print_function, unicode_literals, absolute_import

import doit.tools
import os
import os.path
import re
import shutil
import sys

from filetreesubs import utils


class FileTreeSubs(object):
    """Keeps track of all settings and data, and generates tasks."""

    # Default configuration
    source = 'input'
    destination = 'output'
    substitutes = dict()
    substitute_chains = []
    create_index_filename = None
    create_index_content = ''
    doit_config_update = {}
    encoding = 'utf-8'

    def _do_copy(self, source, destination):
        """Copy file `source` to `destination`."""
        utils.ensure_file_directory_exists(destination)
        try:
            os.unlink(destination)
        except:
            pass
        shutil.copy2(source, destination)

    def _do_remove(self, fn):
        """Remove file `fn`."""
        try:
            os.unlink(fn)
        except Exception as e:
            print(str(e))

    def _do_remove_dir(self, fn):
        """Remove directory tree `fn`."""
        shutil.rmtree(fn, True)

    def _do_createindex(self, filename):
        """Create index file at filename `filename`."""
        utils.ensure_file_directory_exists(filename)
        utils.write_contents(filename, self.create_index_content, encoding=self.encoding)

    def _do_subs(self, source, destination, replace):
        """Apply substitution `replace` for input `source` and write result to `destination`."""
        utils.ensure_file_directory_exists(destination)
        content = utils.get_contents(source, encoding=self.encoding)
        content = utils.substitute(content, {key: self.substitutes_content[key] for key in replace})
        utils.write_contents(destination, content, encoding=self.encoding)

    def _process_replacement(self, key, value):
        """Processes a replacement.

        Updates `self.substitutes_filenames` and `self.substitutes_content`
        for the replacement value `value` for the replacement key `key`.

        `value` must a dict with either `file` or `text` set.

        Returns a list of files the substitution depends on.
        """
        if not isinstance(value, dict):
            raise Exception("Replacement value for key '{0}' must be a dict, but is of type {1}!".format(key, type(value)))
        if 'file' in value:
            value = value['file']
            self.substitutes_original_filenames.add(value)
            fn = os.path.join(self.source, value)
            self.substitutes_filenames[key] = [fn]
            self.substitutes_content[key] = utils.get_contents(fn, encoding=self.encoding)
            return [fn]
        elif 'text' in value:
            self.substitutes_filenames[key] = []
            self.substitutes_content[key] = value['text']
            return []
        else:
            raise Exception("Cannot interpret replacement '{}'!".format(value))

    def get_tasks(self):
        """Generate a list of doit tasks."""
        # First, set up substitution data
        self.substitutes_filenames = dict()
        self.substitutes_original_filenames = set()
        self.substitutes_content = dict()
        for pattern, subs in self.substitutes.items():
            for key, value in subs.items():
                if key not in self.substitutes_content:
                    self._process_replacement(key, value)
        # Process substitution chains
        for chain in self.substitute_chains:
            file = chain['template']
            substitutes = chain['substitutes']
            files = []
            for key, key_file in substitutes.items():
                assert key not in self.substitutes_content
                files.extend(self._process_replacement(key, key_file))
            fn = os.path.join(self.source, file)
            for key, value in self.substitutes_filenames.items():
                if len(value) > 0 and fn == value[0]:
                    self.substitutes_filenames[key].extend(files)
                    self.substitutes_content[key] = utils.substitute(self.substitutes_content[key], {k: self.substitutes_content[k] for k in substitutes.keys()})

        # Now yield base tasks
        yield {
            'basename': 'copy',
            'name': None,
            'doc': 'Copies modified or non-existing files over',
        }
        yield {
            'basename': 'subs',
            'name': None,
            'doc': 'Makes substitutions',
        }
        yield {
            'basename': 'remove',
            'name': None,
            'doc': 'Removes files that should not exist',
        }
        yield {
            'basename': 'create_index',
            'name': None,
            'doc': 'Create index files',
        }

        # Walk trees to find differences
        destfiles = set()
        destdirs = set()
        subs_matcher = {re.compile(key): value for key, value in self.substitutes.items()}
        # Walk destination tree and store data in destfiles() and destdirs()
        for dirpath, dirnames, filenames in os.walk(self.destination, followlinks=True):
            path = utils.get_relname(dirpath, self.destination)
            destdirs.add(path)
            for filename in filenames:
                destfiles.add(os.path.join(path, filename))
        # Walk source tree and compute differences
        for dirpath, dirnames, filenames in os.walk(self.source, followlinks=True):
            path = utils.get_relname(dirpath, self.source)
            # Check whether the directory still exists
            if path in destdirs:
                destdirs.remove(path)
            # Check whether an index file should be created
            if self.create_index_filename is not None and self.create_index_filename not in filenames:
                fn = os.path.join(path, self.create_index_filename)
                if fn in destfiles:
                    # Avoid deletion task being created
                    destfiles.remove(fn)
                dst_file = os.path.join(self.destination, fn)
                yield {
                    'basename': 'createindex',
                    'name': dst_file,
                    'targets': [dst_file],
                    'actions': [(self._do_createindex, (dst_file, ))],
                    'uptodate': [doit.tools.config_changed({'content': self.create_index_content})],
                }
            # Special case for root: skip substitutes filenames so these files aren't copied/...
            if path == '':
                for value in self.substitutes_original_filenames:
                    if value in filenames:
                        filenames.remove(value)
                    else:
                        print('Unknown substitution file "{0}" in "{1}"!'.format(value, self.source))
                        sys.exit(1)
            # Generate copy/subs tasks
            for filename in sorted(filenames):
                fn = os.path.join(path, filename)
                if fn in destfiles:
                    destfiles.remove(fn)
                src_file = os.path.join(self.source, fn)
                dst_file = os.path.join(self.destination, fn)
                replaces = set()
                for matcher, values in subs_matcher.items():
                    if matcher.match(fn):
                        for key, value in values.items():
                            replaces.add(key)
                if len(replaces) > 0:
                    deps = [src_file]
                    for key in replaces:
                        deps.extend(self.substitutes_filenames[key])
                    yield {
                        'basename': 'subs',
                        'name': dst_file,
                        'file_dep': deps,
                        'targets': [dst_file],
                        'actions': [(self._do_subs, (src_file, dst_file, replaces))],
                    }
                else:
                    yield {
                        'basename': 'copy',
                        'name': dst_file,
                        'file_dep': [src_file],
                        'targets': [dst_file],
                        'actions': [(self._do_copy, (src_file, dst_file))],
                    }
        # Check which files are in destination which shouldn't be there
        for fn in sorted(destfiles):
            dst_file = os.path.join(self.destination, fn)
            yield {
                'basename': 'remove',
                'name': dst_file,
                'actions': [(self._do_remove, (dst_file, ))],
            }
        # Check which subdirectories are in destination which shouldn't be there
        for dir in sorted(destdirs):
            dst_file = os.path.join(self.destination, dir)
            yield {
                'basename': 'remove',
                'name': dst_file,
                'actions': [(self._do_remove_dir, (dst_file, ))],
            }
