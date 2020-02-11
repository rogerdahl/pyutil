# Misc utilities written in Python

## resync

`resync` is a wrapper around rsync and inotify which automatically runs `rsync` whenever something in the source hierarchy changes.

Convenient when editing files locally and testing them on a server. Works well in JetBrains IDEs set to save automatically, as simply switching focus from the IDE to the server window causes the files to get copied to the server.

## Install on Linux

This script works only on Linux.

Assuming you have a `~/bin` dir and it's in your `PATH`:

```
pip install inotify-simple
git clone <this project> ~/resync
sudo ln -sr ~/resync/resync.py ~/bin/resync
```

## Usage

Review the list of rsync switches at the top of the script. Then:

```bash
$ resync <src> <dst>
```

```
usage: resync [-h] [--settle sec] [--debug] src dst

positional arguments:
  src
  dst

optional arguments:
  -h, --help    show this help message and exit
  --settle sec  Required period without additional changes being 
                detected before starting sync
  --debug       Debug level logging
```
