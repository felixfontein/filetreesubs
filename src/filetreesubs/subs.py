# SPDX-License-Identifier: MIT

# Copyright © 2014—2023 Felix Fontein.
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

from __future__ import annotations

import os
import os.path
import re
import shutil
import sys

import doit.tools

from filetreesubs import utils


class FileTreeSubs:
    # pylint:disable=too-few-public-methods
    """Keeps track of all settings and data, and generates tasks."""

    # Default configuration
    source = "input"
    destination = "output"
    substitutes = {}
    substitute_chains = []
    create_index_filename = None
    create_index_content = ""
    doit_config_update = {}
    encoding = "utf-8"

    # Internal vars
    substitutes_filenames = {}
    substitutes_original_filenames = set()
    substitutes_content = {}
    substitutes_content_config = {}

    def _do_copy(self, source, destination):
        """Copy file `source` to `destination`."""
        utils.ensure_file_directory_exists(destination)
        try:
            os.unlink(destination)
        except Exception:  # pylint:disable=broad-exception-caught
            pass
        shutil.copy2(source, destination)

    def _do_remove(self, filename):
        """Remove file `filename`."""
        try:
            os.unlink(filename)
        except Exception as exc:  # pylint:disable=broad-exception-caught
            print(str(exc))

    def _do_remove_dir(self, filename):
        """Remove directory tree `filename`."""
        shutil.rmtree(filename, True)

    def _do_createindex(self, filename):
        """Create index file at filename `filename`."""
        utils.ensure_file_directory_exists(filename)
        utils.write_contents(
            filename, self.create_index_content, encoding=self.encoding
        )

    def _do_subs(self, source, destination, replace):
        """Apply substitution `replace` for input `source` and write result to `destination`."""
        utils.ensure_file_directory_exists(destination)
        content = utils.get_contents(source, encoding=self.encoding)
        content = utils.substitute(
            content, {key: self.substitutes_content[key] for key in replace}
        )
        utils.write_contents(destination, content, encoding=self.encoding)

    def _process_replacement(self, key, value):
        """Processes a replacement.

        Updates `self.substitutes_filenames` and `self.substitutes_content`
        for the replacement value `value` for the replacement key `key`.

        `value` must a dict with either `file` or `text` set.

        Returns a list of files the substitution depends on.
        """
        if not isinstance(value, dict):
            raise RuntimeError(
                f"Replacement value for key '{key}' must be a dict, but is of type {type(value)}!"
            )
        self.substitutes_content_config[key] = value
        if "file" in value:
            value = value["file"]
            self.substitutes_original_filenames.add(value)
            filename = os.path.join(self.source, value)
            self.substitutes_filenames[key] = [filename]
            self.substitutes_content[key] = utils.get_contents(
                filename, encoding=self.encoding
            )
            return [filename]
        if "text" in value:
            self.substitutes_filenames[key] = []
            self.substitutes_content[key] = value["text"]
            return []
        raise RuntimeError(f"Cannot interpret replacement '{value}'!")

    def get_tasks(self):  # noqa: C901
        # pylint:disable=too-many-locals,too-many-branches,too-many-statements
        """Generate a list of doit tasks."""
        # First, set up substitution data
        for pattern, subs in self.substitutes.items():
            for key, value in subs.items():
                if key in self.substitutes_content_config:
                    if self.substitutes_content_config[key] != value:
                        raise RuntimeError(
                            # pylint:disable-next=line-too-long
                            f"Substitution for pattern '{pattern}': substitution '{key}' is already used somewhere else with a different meaning!"
                        )
                    continue
                self._process_replacement(key, value)
        # Process substitution chains
        for chain in self.substitute_chains:
            file = chain["template"]
            substitutes = chain["substitutes"]
            files = []
            for key, key_file in substitutes.items():
                if key in self.substitutes_content_config:
                    if self.substitutes_content_config[key] != key_file:
                        raise RuntimeError(
                            # pylint:disable-next=line-too-long
                            f"Substitution chain for '{file}': substitution '{key}' is already used somewhere else with a different meaning!"
                        )
                    continue
                files.extend(self._process_replacement(key, key_file))
            filename = os.path.join(self.source, file)
            for key, value in self.substitutes_filenames.items():
                if len(value) > 0 and filename == value[0]:
                    value.extend(files)
                    self.substitutes_content[key] = utils.substitute(
                        self.substitutes_content[key],
                        {k: self.substitutes_content[k] for k in substitutes.keys()},
                    )

        # Now yield base tasks
        yield {
            "basename": "copy",
            "name": None,
            "doc": "Copies modified or non-existing files over",
        }
        yield {
            "basename": "subs",
            "name": None,
            "doc": "Makes substitutions",
        }
        yield {
            "basename": "remove",
            "name": None,
            "doc": "Removes files that should not exist",
        }
        yield {
            "basename": "create_index",
            "name": None,
            "doc": "Create index files",
        }

        # Walk trees to find differences
        destfiles = set()
        destdirs = set()
        subs_matcher = {
            re.compile(key): value for key, value in self.substitutes.items()
        }
        # Walk destination tree and store data in destfiles() and destdirs()
        for dirpath, _, filenames in os.walk(self.destination, followlinks=True):
            path = utils.get_relname(dirpath, self.destination)
            destdirs.add(path)
            for filename in filenames:
                destfiles.add(os.path.join(path, filename))
        # Walk source tree and compute differences
        for dirpath, _, filenames in os.walk(self.source, followlinks=True):
            path = utils.get_relname(dirpath, self.source)
            # Check whether the directory still exists
            if path in destdirs:
                destdirs.remove(path)
            # Check whether an index file should be created
            if (
                self.create_index_filename is not None
                and self.create_index_filename not in filenames
            ):
                filename = os.path.join(path, self.create_index_filename)
                if filename in destfiles:
                    # Avoid deletion task being created
                    destfiles.remove(filename)
                dst_file = os.path.join(self.destination, filename)
                yield {
                    "basename": "create_index",
                    "name": dst_file,
                    "targets": [dst_file],
                    "actions": [(self._do_createindex, (dst_file,))],
                    "uptodate": [
                        doit.tools.config_changed(
                            {"content": self.create_index_content}
                        )
                    ],
                }
            # Special case for root: skip substitutes filenames so these files aren't copied/...
            if path == "":
                for value in self.substitutes_original_filenames:
                    if value in filenames:
                        filenames.remove(value)
                    else:
                        print(
                            f'Unknown substitution file "{value}" in "{self.source}"!'
                        )
                        sys.exit(1)
            # Generate copy/subs tasks
            for filename in sorted(filenames):
                filename = os.path.join(path, filename)
                if filename in destfiles:
                    destfiles.remove(filename)
                src_file = os.path.join(self.source, filename)
                dst_file = os.path.join(self.destination, filename)
                replaces = set()
                for matcher, values in subs_matcher.items():
                    if matcher.match(filename):
                        for key, value in values.items():
                            replaces.add(key)
                if len(replaces) > 0:
                    deps = [src_file]
                    for key in replaces:
                        deps.extend(self.substitutes_filenames[key])
                    yield {
                        "basename": "subs",
                        "name": dst_file,
                        "file_dep": deps,
                        "targets": [dst_file],
                        "actions": [(self._do_subs, (src_file, dst_file, replaces))],
                    }
                else:
                    yield {
                        "basename": "copy",
                        "name": dst_file,
                        "file_dep": [src_file],
                        "targets": [dst_file],
                        "actions": [(self._do_copy, (src_file, dst_file))],
                    }
        # Check which files are in destination which shouldn't be there
        for filename in sorted(destfiles):
            dst_file = os.path.join(self.destination, filename)
            yield {
                "basename": "remove",
                "name": dst_file,
                "actions": [(self._do_remove, (dst_file,))],
            }
        # Check which subdirectories are in destination which shouldn't be there
        for directory in reversed(sorted(destdirs)):
            dst_file = os.path.join(self.destination, directory)
            yield {
                "basename": "remove",
                "name": dst_file,
                "actions": [(self._do_remove_dir, (dst_file,))],
            }
