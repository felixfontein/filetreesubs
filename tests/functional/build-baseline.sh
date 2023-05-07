#!/bin/bash
# Copyright © 2023 Felix Fontein.
# SPDX-License-Identifier: MIT

set -e


TEMPDIR="$(mktemp -d filetreesubs-baseline-XXXXXXXXXX)"

trap "{ rm -rf ${TEMPDIR}; }" EXIT


make_baseline() {
    DEST="$1"
    shift
    SOURCE="$1"
    shift
    CONFIG="$1"

    echo "Building baseline ${DEST}..."
    cp -r "${SOURCE}" "${TEMPDIR}/${SOURCE}"
    cp -r "${CONFIG}" "${TEMPDIR}/${CONFIG}"
    find "${TEMPDIR}/${SOURCE}" -name '.keep' -delete
    ( cd "${TEMPDIR}" ; filetreesubs "$@" > /dev/null )
    rsync -acv --delete "${TEMPDIR}/${DEST}/" "${DEST}/"
}


make_baseline baseline-base baseline-base-source baseline-base.yaml
make_baseline baseline-index baseline-index-source baseline-index.yaml
make_baseline baseline-full baseline-full-source baseline-full.yaml
