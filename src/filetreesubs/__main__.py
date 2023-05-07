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

"""The main CLI interface of file tree substitutions"""

from __future__ import annotations

import sys

import doit.cmd_base
import doit.doit_cmd
import doit.loader
import doit.reporter
import yaml

import filetreesubs.subs


class FileTreeSubsTaskLoader(doit.cmd_base.TaskLoader2):
    # pylint: disable=too-few-public-methods
    """Load tasks and doit config."""

    def __init__(self, file_tree_subs):
        super().__init__()
        self.file_tree_subs = file_tree_subs

    def load_doit_config(self):
        doit_config = {
            "reporter": doit.reporter.ExecutedOnlyReporter,
            "outfile": sys.stderr,
            "default_tasks": ["subs", "copy", "remove", "create_index"],
        }
        doit_config.update(self.file_tree_subs.doit_config_update)
        return doit_config

    def load_tasks(self, cmd, pos_args):  # pylint:disable=unused-argument
        """
        Load task.
        """
        return doit.loader.generate_tasks("main", self.file_tree_subs.get_tasks())


class FileTreeSubsDoitCmd(doit.doit_cmd.DoitMain):
    """Doit command for executing tasks."""

    TASK_LOADER = FileTreeSubsTaskLoader

    def __init__(self, file_tree_subs):
        super().__init__()
        self.file_tree_subs = file_tree_subs
        self.task_loader = self.TASK_LOADER(file_tree_subs)

    def run(self, all_args=None):
        return super().run(["run"])


def _load_config(file_tree_subs, config):
    if "source" in config:
        file_tree_subs.source = config["source"]
    if "destination" in config:
        file_tree_subs.destination = config["destination"]
    if "substitutes" in config:
        file_tree_subs.substitutes = config["substitutes"]
    if "substitute_chains" in config:
        file_tree_subs.substitute_chains = config["substitute_chains"]
    if "create_index_filename" in config:
        file_tree_subs.create_index_filename = config["create_index_filename"]
    if "create_index_content" in config:
        file_tree_subs.create_index_content = config["create_index_content"]
    if "doit_config" in config:
        file_tree_subs.doit_config_update = config["doit_config"]
    if "encoding" in config:
        file_tree_subs.encoding = config["encoding"]


def main(args=None):  # noqa: C901
    """The main CLI program."""
    if args is None:
        args = sys.argv[1:]
    try:
        # Parse arguments
        config_filename = "filetreesubs-config.yaml"
        if len(args) >= 1:
            config_filename = args[0]
        for arg in args[1:]:
            raise RuntimeError(f"Unknown argument '{arg}'!")

        # Load configuration
        with open(config_filename, "rb") as file:
            try:
                config = yaml.safe_load(file)
            except Exception as exc:  # pylint:disable=broad-exception-caught
                raise RuntimeError(
                    "Failure while parsing '{0}':\n{1}".format(
                        config_filename,
                        "\n".join(["  " + line for line in str(exc).split("\n")]),
                    )
                ) from exc

        # Use configuration
        file_tree_subs = filetreesubs.subs.FileTreeSubs()
        _load_config(file_tree_subs, config)

        # Execute substitution
        return FileTreeSubsDoitCmd(file_tree_subs).run()
    except Exception as exc:  # pylint:disable=broad-exception-caught
        sys.stderr.write(f"{exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
