# AGENTS instructions

- Confirm that you have read these instructions.
- Always ask for approval before modifying any files.

## Project Overview

- We are using P4Transfer.py script to mirror a Perforce stream depot from a Windows Perforce server to a Linux Perforce server.

### Repository Structure

Key paths and descriptions:

- `P4Transfer.py` — Main script. Transfers Perforce changelists with full history between independent servers (source → target) when remote depots and DVCS commands are not an option.
- `CompareRepos.py` — Companion script to P4Transfer. Compares changelists in source and target repos to verify correctness. Reads the same config file.
- `FetchTransfer.py` — Alternative transfer script that wraps `p4 fetch` (requires Helix Core 2015.1+ with DVCS support). Use P4Transfer.py when DVCS is not available.
- `ParseDiffs.py` — Utility to parse and compare depot file listings (actions, sizes, digests) between source and target.
- `logutils.py` — Shared logging utilities used by the main scripts.
- `transfer.yaml` — **Live config file.** May contain sensitive data (server addresses, credentials). Only modify if explicitly agreed with the user.
- `doc/` — AsciiDoc documentation, generated HTML/PDF, and help text files. See `doc/P4Transfer.adoc` for full usage guide.
- `test/` — Unit tests (unittest framework). See [Testing](#testing) below.
- `experimental/` — Experimental/work-in-progress scripts.
- `utils/` — Utility scripts.
- `map_changes.sh` — Shell script to extract target/source change mappings from transferred changelists.
- `run_compare.sh` — Shell script to run CompareRepos against all depot paths in a target client.
- `summarise_log.sh` — Shell script to summarise a P4Transfer log for reporting failures.
- `requirements.txt` — Python dependencies.
- `README.md` — Project readme.

## Environment Setup

- We're using a python virtual environment at ./.venv
- Install dependencies: `pip install -r requirements.txt`
- Dependencies: `ruamel.yaml`, `requests`, `p4python`

### Running P4Transfer

For production use on Linux over SSH:

```bash
nohup env P4IGNORE=/dev/null python3 P4Transfer.py -c transfer.yaml --repeat > out.log 2>&1 &
```

For local development (omit nohup and background):

```bash
python3 P4Transfer.py -c transfer.yaml > out.log 2>&1
```

Key flags: `-r`/`--repeat` (continuous polling loop), `-n`/`--notransfer` (validate only), `-m N`/`--maximum N` (limit changes), `-s`/`--stoponerror`, `--sample-config` (print example config).

### Testing

Tests use Python's `unittest` framework. Test files are in `test/`:

- `test/TestP4Transfer.py` — Tests for P4Transfer.py
- `test/TestCompareRepos.py` — Tests for CompareRepos.py
- `test/TestFetchTransfer.py` — Tests for FetchTransfer.py

Run tests:

```bash
python -m pytest test/
# or
python -m unittest discover test/
```

Note: Tests require a running Perforce server (`p4d`) and the `P4` (p4python) module.

## Coding Conventions

- Python 3.6+ compatible (some code also supports Python 2.7 but 3.x is the target).
- Linter: **flake8** (config in `.flake8`: `max-line-length = 160`).
- Follow PEP 8 style, respecting the project's 160-char line length.
- Match existing code style in the file you are editing.
- Wrap any consecutive lines (as well as single lines) containing code changes within annotation comments in the form `YAGER START - [aigenerated] - <dd/mm/yyyy> - <Short description>` and `YAGER END <...>` respectively.

## Boundaries

- Never
    - Commit secrets, credentials, or tokens.
    - Edit generated files by hand when a generation workflow exists.
    - Use destructive git operations unless explicitly requested.
    - Modify `transfer.yaml` without explicit user agreement (it is a live config that may contain sensitive data).
