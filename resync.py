#!/usr/bin/env python

import argparse
import logging
import os
import pathlib
import subprocess

import inotify_simple

DEFAULT_RSYNC_SWITCHES = [
    "--recursive",
    "--verbose",
    "--progress",
    "--links",
    "--times",
    "--omit-dir-times",
]

DEFAULT_SETTLE_SEC = 1.0

f = inotify_simple.flags
WATCH_FLAGS = (
    f.MODIFY
    | f.MOVE_SELF
    | f.MOVED_FROM
    | f.MOVED_TO
    | f.CREATE
    | f.CLOSE_WRITE
    # We don't delete anything on the destination, so don't have to sync on local
    # delete.
    # | f.DELETE
    # | f.DELETE_SELF
)


EXCLUDE_FILE_PATH = pathlib.Path(__file__).resolve().parent / "resync-exclude.txt"


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("src_path", metavar="src")
    parser.add_argument("dst_path", metavar="dst")
    parser.add_argument(
        "--settle",
        dest="settle_sec",
        metavar="sec",
        type=float,
        default=DEFAULT_SETTLE_SEC,
        help=(
            "Required period without additional changes being detected before starting "
            "sync"
        ),
    )
    parser.add_argument("--debug", action="store_true", help="Debug level logging")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)-8s %(message)s",
    )

    inotify = inotify_simple.INotify()

    watch_list = []
    try:
        watch_list = add_watches(inotify, args.src_path)

        try:
            while True:
                log.info("Synchronizing...")
                run_rsync(args.src_path, args.dst_path)
                wait_for_change(inotify, args.settle_sec)

        except Exception:
            raise

    finally:
        delete_watches(inotify, watch_list)


def run_rsync(src_path, dst_path):
    cmd_list = [
        "rsync",
        *DEFAULT_RSYNC_SWITCHES,
        "--exclude-from",
        EXCLUDE_FILE_PATH,
        src_path,
        dst_path,
    ]
    subprocess.run(cmd_list)


def add_watches(inotify, src_path):
    f = inotify_simple.flags
    watch_list = []
    for root_path, dir_list, file_list in os.walk(src_path):
        log.debug(f"Watching: {root_path}")
        w = inotify.add_watch(root_path, WATCH_FLAGS)
        watch_list.append(w)
    return watch_list


def wait_for_change(inotify, settle_sec):
    log.info("Waiting for filesystem change...")

    has_changed = False
    timeout_sec = 0.1

    while True:
        i_event_list = inotify.read(timeout=int(timeout_sec * 1000))

        if (not i_event_list) and has_changed:
            log.debug("Changes have settled")
            break

        for i_event in i_event_list:
            has_changed = True
            timeout_sec = settle_sec

            flag_tup = inotify_simple.flags.from_mask(i_event.mask)
            str_gen = (f.name.lower() for f in flag_tup)
            log.debug(f"Changed: {i_event.name} ({' '.join(str_gen)})")
            log.debug("Waiting for changes to settle...")


def delete_watches(inotify, watch_list):
    for w in watch_list:
        log.debug(f"Deleting watch: {w}")
        inotify.rm_watch(w)


if __name__ == "__main__":
    main()
