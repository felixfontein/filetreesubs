<!--
Copyright © 2014—2023 Felix Fontein.
SPDX-License-Identifier: MIT
-->

File Tree Subs
==============

[![Tests badge](https://github.com/felixfontein/filetreesubs/actions/workflows/python.yml/badge.svg)](https://github.com/felixfontein/filetreesubs/actions/workflows/python.yml)
[![Codecov badge](https://img.shields.io/codecov/c/github/felixfontein/filetreesubs)](https://codecov.io/gh/felixfontein/filetreesubs)

Allows to synchronize a destination file tree from a source file tree while allowing certain substitutions to take place.

File Tree Subs uses [doit](http://pydoit.org/) under the hood to keep track of changes, so that files are only changed if necessary.

See the following three examples for typical use cases of `filetreesubs`. I'm personally using it to preprocess the output of [Nikola](https://getnikola.com/), a static blog/site generator, to insert a sidebar into all generated HTML pages, and a tag cloud into the sidebar and the tag overview page.

To install, use `pip install filetreesubs`.


Example
-------

Assume you have the following file tree:

    input/
        index.html
        team.html
        products.html
        menu.inc
        testimonials.inc

In the `.html` files, you put placeholder strings `INSERT_MENU_HERE` for where the content of `input/menu.inc` should be inserted, and `INSERT_TESTIMONIALS` for where the content of `input/testimonials.inc` should be inserted. Also, you want `COPYRIGHT_YEAR` to be replaced by 2017. The result should be a tree like this, without the `.inc` files:

    output/
        index.html
        team.html
        products.html

with the placeholder string replaced. To do this with `filetreesubs`, create a config file `filetreesubs-config.yaml`:

```yaml
# Source directory
source: input
# Destination directory
destination: output
substitutes:
  # The following is a regular expression to match the filenames:
  '.*\.html':
    # The strings to replace
    'INSERT_MENU_HERE':
      # With what to replace them
      file: menu.inc
    'INSERT_TESTIMONIALS':
      file: testimonials.inc
    'COPYRIGHT_YEAR':
      text: '2017'
```

Then running `filetreesubs` will synchronize `output/` so that it contains the files from `input/`, except `menu.inc`, and makes sure the substitutions take place.


Example: Sidebar in Nikola
--------------------------

You can find an example site for Nikola using the [sidebar plugin](https://plugins.getnikola.com/v8/sidebar/) in [the Github repository felixfontein/filetreesubs-nikola-demo](https://github.com/felixfontein/filetreesubs-nikola-demo/).

A more complex, but less explicit example can be found [in my blog](https://spielwiese.fontein.de/2017/01/06/static-sidebar-and-tag-cloud/), which also includes a tag cloud (rendered by the [static_tag_cloud pugin](https://plugins.getnikola.com/v8/static_tag_cloud/)) into the sidebar.


Example: Substitution chains
----------------------------

Assume that in the above example, you want to use `INSERT_TESTIMONIALS` also in `menu.inc` itself. Running the above example, this substitution will not be done, also if you extend the regular expression matching all HTML files to `.*` to match all files.

To apply substitutions to included files, you need to use substitution chains. Append the following to the configuration above:

```yaml
substitute_chains:
- template: menu.inc
  substitutes:
    'INSERT_TESTIMONIALS':
      file: testimonials.inc
```

This will apply the substitution for `INSERT_TESTIMONIALS` also to `menu.inc`.


Example: Creating index files
-----------------------------

Assume that you have folder structure:

    input/
        index.html
        images/
            logo.jpeg
            2017/
                happynewyear-2017.jpeg

You want to upload the output to a web server so it is available under `http://example.com`, but if someone accesses `http://example.com/images/` or `http://example.com/images/2017/`, you don't want the persons to see a file listing or some error page, but show them a nice message to check out the home page. You can use `filetreesubs` for this. Add the following to the configuration:

```yaml
create_index_filename: index.html
create_index_content: |
  <!DOCTYPE html>
  <html>
    <head>
      <title>There's nothing to see here.</title>
      <meta http-equiv="refresh" content="10; url=..">
    </head>
    <body>
      There's nothing to see here. Go <a href="..">here</a> instead.
      You will be automatically redirected there in 10 seconds.
    </body>
  </html>
```

Then in every folder not containing a file `index.html`, a file `index.html` will be created with the specified content.


Configuration file format
-------------------------

The configuration file is in [YAML format](https://en.wikipedia.org/wiki/YAML). By default, the configuration is assumed to be in `filetreesubs-config.yaml` in the current directory. If you want to specify a different configuration file name, you can simply specify it on the command line:

    filetreesubs my-config-file.yaml

The following commented YAML file shows all available options:

```yaml
# The source directory. Specify a path here.
source: input

# The destination directory. Specify a path here.
destination: output

# The substitutions to make
substitutes:
  # For every substitution, you need to specify a regex pattern
  # matching the file name. Use '.*' to match everything, and
  # '.*\.html' to match all files ending with '.html'.
  '.*':
    # Now you can specify a number of strings which shall be replaced
    'STRING TO REPLACE':
      # In this case, we want to replace the string by the contents
      # of the file menu.inc. Note that menu.inc won't be copied
      # to the destination directory anymore.
      file: menu.inc
    'ANOTHER_REPLACEMENT_STRING':
      # In this case, we want to replace the string by another string
      # we explicitly specify here.
      text: '(replacement text)'
  # Now we can specify more filename matching patterns ...
  '.*\.html':
    # ... and more replacements
    'YET_ANOTHER_STRING':
      text: '(some more)'

# To do substitutions in files like menu.inc, we need substitution
# chains.
substitute_chains:
# Each substitution chain consists of the name of the file to
# substitute in, like menu.inc:
- template: menu.inc
  # As well as a list of substitutions, using the same syntax as above:
  substitutes:
    # The string to replace:
    'INCLUDE_INCLUDE':
      # What to replace it with
      file: include.inc
    'INCLUDE_STRING':
      text: '...'
# You can have as many substitution chains as you want
- template: include.inc
  substitutes:
    'ONE_MORE':
      text: '(...)'

# To create index files (when not already existing), you must
# specify the name of these files:
create_index_filename: index.html

# This allows to specify the content of index files.
create_index_content: |
  <!DOCTYPE html>
  <html lang="en">
    <head>
      <title>there's nothing to see here.</title>
      <meta name="robots" content="noindex">
      <meta http-equiv="refresh" content="0; url=..">
    </head>
    <body style="background-color:black; color:white;">
      <div style="position:absolute; top:0; left:0; right:0; bottom:0;">
        <div style="width:100%; height:100%; display:table;">
            there's nothing to see here. go <a href=".." style="color:#AAA;">here</a> instead.
          </div>
        </div>
      </div>
    </body>
  </html>

# By default, filetreesubs assumes that all text files it processes
# are UTF-8 encoded. If that's not the case, you can change another
# encoding here.
encoding: utf-8

# In case you need to do so, you can insert configurations for doit
# directly here. See `here <http://pydoit.org/configuration.html#configuration-at-dodo-py>`__
# for possible configurations.
doit_config:
  # The following option sets the filename for the dependency database.
  # If you want to execute different filetreesubs commands concurrently
  # from a folder, you need to specify different dependency database
  # names per project config.
  dep_file: '.doit-myproject.db'
```
