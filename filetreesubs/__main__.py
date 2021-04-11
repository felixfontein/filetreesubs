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

"""The main CLI interface of file tree substitutions"""

from __future__ import print_function, unicode_literals, absolute_import

import doit.cmd_base
import doit.doit_cmd
import doit.loader
import doit.reporter
import filetreesubs.subs
import sys
import yaml


class FileTreeSubsTaskLoader(doit.cmd_base.TaskLoader):
    """Load tasks and doit config."""

    def __init__(self, file_tree_subs):
        self.file_tree_subs = file_tree_subs

    def load_tasks(self, cmd, opt_values, pos_args):
        DOIT_CONFIG = {
            'reporter': doit.reporter.ExecutedOnlyReporter,
            'outfile': sys.stderr,
            'default_tasks': ['subs', 'copy', 'remove', 'createindex'],
        }
        DOIT_CONFIG.update(self.file_tree_subs.doit_config_update)
        tasks = doit.loader.generate_tasks('main', self.file_tree_subs.get_tasks())
        return tasks, DOIT_CONFIG


class FileTreeSubsDoitCmd(doit.doit_cmd.DoitMain):
    """Doit command for executing tasks."""

    TASK_LOADER = FileTreeSubsTaskLoader

    def __init__(self, file_tree_subs):
        super(FileTreeSubsDoitCmd, self).__init__()
        self.file_tree_subs = file_tree_subs
        self.task_loader = self.TASK_LOADER(file_tree_subs)

    def run(self):
        return super(FileTreeSubsDoitCmd, self).run(["run"])


def main(args=None):
    """The main CLI program."""
    if args is None:
        args = sys.argv[1:]
    try:
        # Parse arguments
        config_filename = 'filetreesubs-config.yaml'
        if len(args) >= 1:
            config_filename = args[0]
        for arg in args[1:]:
            raise Exception("Unknown argument '{}'!".format(arg))

        # Load configuration
        with open(config_filename, "rb") as f:
            try:
                config = yaml.safe_load(f)
            except Exception as e:
                raise Exception("Failure while parsing '{0}':\n{1}".format(config_filename, '\n'.join(['  ' + line for line in str(e).split('\n')])))

        # Use configuration
        file_tree_subs = filetreesubs.subs.FileTreeSubs()
        if 'source' in config:
            file_tree_subs.source = config['source']
        if 'destination' in config:
            file_tree_subs.destination = config['destination']
        if 'substitutes' in config:
            file_tree_subs.substitutes = config['substitutes']
        if 'substitute_chains' in config:
            file_tree_subs.substitute_chains = config['substitute_chains']
        if 'create_index_filename' in config:
            file_tree_subs.create_index_filename = config['create_index_filename']
        if 'create_index_content' in config:
            file_tree_subs.create_index_content = config['create_index_content']
        if 'doit_config' in config:
            file_tree_subs.doit_config_update = config['doit_config']
        if 'encoding' in config:
            file_tree_subs.encoding = config['encoding']

        # Execute substitution
        return FileTreeSubsDoitCmd(file_tree_subs).run()
    except Exception as e:
        sys.stderr.write(str(e) + '\n')


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
