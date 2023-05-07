# Copyright © 2014—2023 Felix Fontein.
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
from pathlib import Path

import nox

nox.options.sessions = ["lint"]


def install(session: nox.Session, *args, editable=False, **kwargs):
    if editable and session.interactive:
        args = ("-e", *args)
    session.install(*args, "-U", **kwargs)


@nox.session(python=["3.9", "3.10", "3.11"])
def test(session: nox.Session):
    install(
        session,
        ".[test, coverage]",
        editable=True,
    )
    covfile = Path(session.create_tmp(), ".coverage")
    session.run(
        "pytest",
        "--cov-branch",
        "--cov=filetreesubs",
        "--cov-report",
        "term-missing",
        "--error-for-skips",
        *session.posargs,
        env={"COVERAGE_FILE": f"{covfile}", **session.env},
    )


@nox.session
def coverage(session: nox.Session):
    install(session, ".[coverage]", editable=True)
    combined = map(str, Path().glob(".nox/*/tmp/.coverage"))
    session.run("coverage", "combine", "--keep", *combined)
    session.run("coverage", "xml")
    session.run("coverage", "report", "-m")


@nox.session
def lint(session: nox.Session):
    session.notify("formatters")
    session.notify("codeqa")


@nox.session
def formatters(session: nox.Session):
    install(session, ".[formatters]")
    posargs = list(session.posargs)
    if not session.interactive:
        posargs.append("--check")
    session.run("isort", *posargs, "src", "tests", "noxfile.py")
    session.run("black", *posargs, "src", "tests", "noxfile.py")


@nox.session
def codeqa(session: nox.Session):
    install(session, ".[codeqa]", editable=True)
    session.run("flake8", "src/filetreesubs", "tests", *session.posargs)
    session.run(
        "pylint",
        "src/filetreesubs",
    )
    session.run("reuse", "lint")
