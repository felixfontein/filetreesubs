#!/bin/bash
set -e
poetry run flake8 filetreesubs --count --max-line-length=180 --statistics "$@"
