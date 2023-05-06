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

"""Utility functions"""

from __future__ import annotations

import os
import os.path


def makedirs(path):
    """Create a folder."""
    if not path:
        return
    if os.path.exists(path):
        if not os.path.isdir(path):
            raise OSError(f"Path {path} already exists and is not a folder.")
        return
    try:
        os.makedirs(path)
        return
    except Exception:
        if os.path.isdir(path):
            return
        raise


def get_relname(path, relative_to):
    """Get relative path name, where '.' is converted to ''."""
    path = os.path.relpath(path, relative_to)
    if path == ".":
        path = ""
    return path


def ensure_file_directory_exists(filename):
    """Ensure that the directory for the given file name exists."""
    makedirs(os.path.dirname(filename))


def substitute(text, replacements):
    """Apply the given replacements to the string `text`."""
    index = 0
    while index < len(text):
        # Search
        search_index = len(text)
        search_text = None
        for search in replacements.keys():
            i = text.find(search, index, search_index + len(search))
            if 0 <= i < search_index:
                search_index = i
                search_text = search
        if search_index == len(text):
            break
        # Replace
        replacement = replacements[search_text]
        text = (
            text[:search_index] + replacement + text[search_index + len(search_text) :]
        )
        index = search_index + len(replacement)
    return text


def get_contents(filename, encoding="utf-8"):
    """Retrieve the file content's as a decoded string."""
    with open(filename, "rb") as file:
        return file.read().decode(encoding)


def write_contents(filename, content, encoding="utf-8"):
    """Write the file content to the given string. Will use the specified encoding."""
    try:
        os.unlink(filename)
    except Exception:  # pylint:disable=broad-exception-caught
        pass
    with open(filename, "wb") as file:
        file.write(content.encode(encoding))
