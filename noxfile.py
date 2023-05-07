# Copyright © 2014—2023 Felix Fontein.
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os

import nox

nox.options.sessions = ["lint"]


def install(session: nox.Session, *args, editable=False, **kwargs):
    if editable and session.interactive:
        args = ("-e", *args)
    session.install(*args, "-U", **kwargs)


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
    session.run("isort", *posargs, "src", "noxfile.py")
    session.run("black", *posargs, "src", "noxfile.py")


@nox.session
def codeqa(session: nox.Session):
    install(session, ".[codeqa]", editable=True)
    session.run("flake8", "src/filetreesubs", *session.posargs)
    session.run(
        "pylint",
        "src/filetreesubs",
    )
    session.run("reuse", "lint")
