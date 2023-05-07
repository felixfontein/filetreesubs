# Copyright © 2023 Felix Fontein.
# SPDX-License-Identifier: MIT

from __future__ import annotations

import difflib
import os
import shutil
from contextlib import contextmanager

import pytest

from filetreesubs.__main__ import main

TEST_CASES = [
    (
        ["baseline-base.yaml"],
        "baseline-base.yaml",
        "baseline-base-source",
        "baseline-base",
        0,
        [],
        [],
    ),
    (
        ["baseline-index.yaml"],
        "baseline-index.yaml",
        "baseline-index-source",
        "baseline-index",
        0,
        [],
        [],
    ),
    (
        ["baseline-full.yaml"],
        "baseline-full.yaml",
        "baseline-full-source",
        "baseline-full",
        0,
        [
            "sub",
            "foo",
            "foo/bar",
            "foo/bar/baz",
        ],
        [
            ("index.html", b"Foo"),
            ("sub/index.html", b"Bar"),
            ("foo/index.html", b"Some random file."),
        ],
    ),
]


def _scan_directories(root: str):
    result = {}
    for path, dirs, files in os.walk(root):
        result[os.path.relpath(path, root)] = (path, files)
    return result


def _compare_files(source, dest, path):
    with open(source) as f:
        src = f.read()
    with open(dest) as f:
        dst = f.read()
    if src == dst:
        return 0
    for line in difflib.unified_diff(src.splitlines(), dst.splitlines(), path, path):
        if line[0] == "@":
            print(line)
        elif line[0] == "-":
            print(f"\033[41m\033[9m{line}\033[29m\033[49m")
        elif line[0] == "+":
            print(f"\033[42m{line}\033[49m")
        else:
            print(line)
    return 1


def _compare_directories(source, dest):
    differences = 0
    for path in source:
        if path not in dest:
            print(f"Directory {path} exists only in the baseline!")
            differences += 1
            continue
        source_files = set(source[path][1])
        dest_files = set(dest[path][1])
        for file in source_files:
            if file not in dest_files:
                differences += 1
                print(f"File {os.path.join(path, file)} exists only in the baseline!")
                continue
            source_path = os.path.join(source[path][0], file)
            dest_path = os.path.join(dest[path][0], file)
            differences += _compare_files(
                source_path, dest_path, os.path.join(path, file)
            )
        for file in dest_files:
            if file not in source_files:
                differences += 1
                print(
                    f"File {os.path.join(path, file)} exists only in the generated result!"
                )
    for path in dest:
        if path not in source:
            print(f"Directory {path} exists only in the generated result!")
            differences += 1
            continue
    if differences:
        print(f"Found {differences} differences.")
    assert differences == 0


@contextmanager
def change_cwd(directory):
    old_dir = os.getcwd()
    os.chdir(directory)
    yield
    os.chdir(old_dir)


@pytest.mark.parametrize(
    "arguments, config, source_directory, dest_directory, expected_rc, dirs_to_create, files_to_create",
    TEST_CASES,
)
def test_baseline(
    arguments,
    config,
    source_directory,
    dest_directory,
    expected_rc,
    dirs_to_create,
    files_to_create,
    tmp_path,
):
    tests_root = os.path.join("tests", "functional")

    shutil.copytree(
        os.path.join(tests_root, source_directory),
        tmp_path / source_directory,
        symlinks=True,
        ignore_dangling_symlinks=True,
    )
    shutil.copyfile(os.path.join(tests_root, config), tmp_path / config)
    for path, _, files in os.walk(tmp_path / source_directory):
        if ".keep" in files:
            os.unlink(os.path.join(path, ".keep"))

    for directory in dirs_to_create:
        (tmp_path / dest_directory / directory).mkdir(parents=True, exist_ok=True)

    for file, content in files_to_create:
        with (tmp_path / dest_directory / file).open("wb") as f:
            f.write(content)

    # Re-build baseline
    with change_cwd(str(tmp_path)):
        rc = main(arguments)
    assert rc == expected_rc

    # Compare baseline to expected result
    source = _scan_directories(os.path.join(tests_root, dest_directory))
    dest = _scan_directories(str(tmp_path / dest_directory))
    _compare_directories(source, dest)
