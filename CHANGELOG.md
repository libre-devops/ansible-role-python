# Changelog

Notable changes to this role. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## Unreleased

### Added

- A bootstrap that finds or installs a Python the running ansible-core can use, with `raw` and `script` only, and sets `ansible_python_interpreter`. It works out the oldest Python ansible-core accepts from its version, and installs from the host's repositories (including Satellite or a mirror), package files pushed from the control node, or a python-build-standalone archive pushed from the control node.
- uv, downloaded once on the control node and checked against its SHA-256, or from the host's repositories, and `/etc/uv/uv.toml`.
- Python versions from uv, the host's repositories, pushed package files or pushed archives, with each interpreter recorded in `python_interpreters`.
- Virtual environments owned by the account that uses them, from packages or a requirements file, optionally exact, and removal.
- Molecule scenarios on RHEL 8, 9 and Rocky 10, Debian 12 and 13, Ubuntu 24.04 and 26.04, and SLES 15 and 16, from minimal images with no Python added, and a scenario for pushed packages and archives.
- `docs/using-without-galaxy.md`.

### Changed

- A check-mode run on a host that needs Python installed stops with a message saying so, instead of a missing interpreter.
