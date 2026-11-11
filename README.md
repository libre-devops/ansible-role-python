<div align="center">
  <a href="https://libredevops.org">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://libredevops.org/assets/libre-devops-white.png">
      <img alt="Libre DevOps" src="https://libredevops.org/assets/libre-devops-black.png" width="300">
    </picture>
  </a>
</div>

# Ansible Role: Python

Gives each host a Python that the running ansible-core can use, even hosts with no Python or only an old one such as RHEL 8's 3.6, from wherever your hosts get software: their own repositories (the distribution's, a Red Hat Satellite or a mirror), package files pushed from the control node, or a self-contained build. Then installs uv, more Python versions and virtual environments.

[![CI](https://github.com/libre-devops/ansible-role-python/actions/workflows/ci.yml/badge.svg)](https://github.com/libre-devops/ansible-role-python/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/libre-devops/ansible-role-python?sort=semver&label=release)](https://github.com/libre-devops/ansible-role-python/releases/latest)
[![Galaxy](https://img.shields.io/badge/galaxy-libre__devops.python-EE0000?logo=ansible&logoColor=white)](https://galaxy.ansible.com/ui/standalone/roles/libre_devops/python/)
[![Licence](https://img.shields.io/github/license/libre-devops/ansible-role-python)](./LICENSE)

---

## What it does

1. **Bootstrap.** With `raw` only, it reads the distribution and every Python on the host, and works out the oldest Python the running ansible-core accepts (3.9 for ansible-core 2.20 and later). It keeps a Python that is new enough. Otherwise it installs one from the source you choose, then sets `ansible_python_interpreter` and gathers facts, so every task and role after it just works.
2. **uv.** Installs a pinned uv, checked against its SHA-256. The control node downloads it once and copies it to the hosts, so they need no internet access. Or it installs uv from the host's own repositories.
3. **Python versions.** Installs more versions, each from uv, the host's repositories, pushed package files or a pushed archive, and records each one's interpreter in `python_interpreters`.
4. **Virtual environments.** Makes venvs with uv, owned by the account that uses them, from a list of packages or a requirements file, exactly or not, and removes the ones marked absent.

Each part is optional. On its own, the bootstrap is a fix for "ansible-core cannot use the Python on this host".

## Contents

- [Requirements](#requirements)
- [Supported platforms](#supported-platforms)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Where Python comes from](#where-python-comes-from)
- [Role variables](#role-variables)
- [Python versions](#python-versions)
- [Virtual environments](#virtual-environments)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Developing](#developing)
- [Releasing](#releasing)
- [Credits](#credits)

## Requirements

| What | Detail |
|---|---|
| Control node | `ansible-core` 2.16 or later. No collections. Python on the control node (which ansible-core already has) packs pushed files. |
| Managed nodes | `/bin/sh`. For `files` and `archive`, `base64` (coreutils, on every distribution), and `tar` for an archive. `sudo` or a root connection, as the role installs software. |
| Play | `gather_facts: false`, with the role first. Gathering facts is a module, so on a host with no usable Python it fails before the role can install one. The role gathers facts itself once the interpreter is set. |
| Privileges | `become: true`. |

## Supported platforms

Each platform below runs in CI on every pull request, starting from the distribution's minimal container image with no Python added.

| Distribution | Python before | After the bootstrap, from the host's repositories |
|---|---|---|
| RHEL 8 (UBI) | 3.6 (`/usr/libexec/platform-python`) only | `/usr/bin/python3.12` (`python3.12` from AppStream) |
| RHEL 9 (UBI) | 3.9 | `/usr/bin/python3`, unchanged |
| Rocky 10 | 3.12 | `/usr/bin/python3`, unchanged |
| Debian 12 and 13 | None | `/usr/bin/python3` (`python3`) |
| Ubuntu 24.04 and 26.04 | None | `/usr/bin/python3` (`python3`) |
| SLES 15 SP7 | 3.6 | `/usr/bin/python3.11` (`python311`) |
| SLES 16 | None | `/usr/bin/python3` (`python3`) |

The `sources` scenario also bootstraps RHEL 8 from pushed RPM files with its repositories switched off, and Debian 12 from a pushed python-build-standalone archive. Other distributions in the same families (Alma, Rocky, Oracle Linux, CentOS Stream, Fedora, openSUSE) are covered by `python_bootstrap_packages` and should work the same way.

## Installation

From Galaxy:

```bash
ansible-galaxy role install libre_devops.python
```

Or pin a release from GitHub, as in [`examples/requirements.yml`](./examples/requirements.yml).

Without Galaxy, or to keep a copy inside your organisation, see [Using the role without Galaxy](./docs/using-without-galaxy.md). It covers git, release archives, requirements files that point at your own servers, AWX and Automation Controller, and execution environments.

## Quick start

```yaml
- name: Give the hosts a usable Python
  hosts: all
  become: true
  gather_facts: false
  roles:
    - role: libre_devops.python
```

Run it as the first play of a playbook, or put the role first in each play. Facts and `ansible_python_interpreter` it sets last for the rest of the run, so later plays can gather facts as usual. To keep the interpreter for later runs too, put it in the inventory, for example `ansible_python_interpreter: /usr/bin/python3.12` in `group_vars/rhel8.yml`.

[`examples/playbook.yml`](./examples/playbook.yml) also shows pushed packages, Python versions and venvs.

## Where Python comes from

The bootstrap installs a Python only when the host has none new enough. `python_bootstrap_source` says where it comes from:

| Source | Where | Needs on the host | Good for |
|---|---|---|---|
| `repos` (default) | The package `python_bootstrap_packages` names, from the host's own repositories | Working repositories: the distribution's, a Red Hat Satellite or SUSE Manager, or a mirror | Most hosts. Security updates arrive with the rest of the system's. |
| `files` | Package files on the control node (`python_bootstrap_files`), pushed and installed with the host's package manager | `base64` | Hosts with no repositories at all. |
| `archive` | A python-build-standalone archive (`python_bootstrap_archive`) on the control node or at a URL the control node downloads, pushed and unpacked | `base64`, `tar` | Any distribution, no packages, the same Python everywhere. |

Nothing is pushed or downloaded by the hosts themselves for `files` and `archive`: the role writes the files into a shell script on the control node and runs it on the host with `ansible.builtin.script`, which works before the host has a Python ansible-core can use.

For `files`, bring the packages from a machine that matches the hosts, with their dependencies. For RHEL 8:

```bash
dnf install --downloadonly --downloaddir=python-rpms python3.12
```

By default they are installed with the host's repositories switched off (`python_bootstrap_files_use_repos: false`), so the list must be complete.

For `archive`, use an `install_only` (or `install_only_stripped`) `.tar.gz` from [python-build-standalone's releases](https://github.com/astral-sh/python-build-standalone/releases), such as `cpython-3.12.16+20261026-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz`, and give its SHA-256 from the release's `SHA256SUMS` in `python_bootstrap_archive_checksum`. On Debian and Ubuntu, Ansible's `apt` module needs `python3-apt`, which works only with the distribution's own Python, so the first `apt` task on a host bootstrapped from an archive installs `python3-apt`, and with it the distribution's `python3`. That happens without help, but leaves the host with two Pythons.

## Role variables

Every variable is validated against [`meta/argument_specs.yml`](./meta/argument_specs.yml) when the role starts. Defaults are in [`defaults/main.yml`](./defaults/main.yml).

### Bootstrap

| Variable | Default | Description |
|---|---|---|
| `python_bootstrap` | `true` | Find or install a Python ansible-core can use, and set `ansible_python_interpreter`. |
| `python_bootstrap_min_version` | `auto` | The oldest Python to accept. `auto` follows the running ansible-core: 3.9 from 2.20, 3.8 for 2.18 and 2.19, 3.7 for 2.17, 3.6 before. |
| `python_bootstrap_interpreter` | `""` | Use this interpreter, installing it from the source if it is missing. Empty: the source's interpreter when present, else `/usr/bin/python3`, else the newest found, else install. |
| `python_bootstrap_source` | `repos` | `repos`, `files` or `archive`. See [Where Python comes from](#where-python-comes-from). |
| `python_bootstrap_packages` | see defaults | For `repos` and `files`, the package and its interpreter by family and major version (`rhel8`), then family (`rhel`, `fedora`, `suse`, `debian`). |
| `python_bootstrap_files` | `[]` | For `files`, the package files on the control node. |
| `python_bootstrap_files_use_repos` | `false` | For `files`, let the package manager fetch missing dependencies from the host's repositories. |
| `python_bootstrap_archive` | `""` | For `archive`, a python-build-standalone `.tar.gz` on the control node, or an `https` URL. |
| `python_bootstrap_archive_checksum` | `""` | For `archive`, such as `sha256:<hex>`. Set it for a URL. |
| `python_bootstrap_archive_dir` | `/opt/python/bootstrap` | For `archive`, where it is unpacked. The interpreter is `<dir>/bin/python3`. |
| `python_bootstrap_gather_facts` | `true` | Gather facts once the interpreter is set. |

### uv

| Variable | Default | Description |
|---|---|---|
| `python_uv_install` | `false` | Install uv even when nothing below needs it. uv is installed anyway for uv Python versions and for venvs. |
| `python_uv_source` | `download` | `download`: the control node fetches the release archive and copies uv to the hosts. `repos`: install `python_uv_package` from the host's repositories (to `/usr/bin/uv`). |
| `python_uv_package` | `uv` | For `repos`, the package name. |
| `python_uv_version` | `0.13.7` | For `download`, the release. |
| `python_uv_checksums` | see defaults | For `download`, the SHA-256 of the archive for `x86_64` and `aarch64`, from the release's `.sha256` files. Change with the version. |
| `python_uv_download_base_url` | GitHub releases | For `download`, `<base>/<version>/uv-<arch>-unknown-linux-gnu.tar.gz`. A mirror of GitHub's releases, or `file:///path` on the control node with the same layout. |
| `python_controller_cache` | `~/.cache/libre_devops.python` | Where the control node keeps downloads and packed scripts. |
| `python_uv_bin_dir` | `/usr/local/bin` | For `download`, where `uv` and `uvx` go. |
| `python_uv_cache_dir` | `/var/cache/uv` | uv's cache on the hosts, with a directory per venv owner. |
| `python_uv_config` | `""` | Written to `/etc/uv/uv.toml`, which uv reads for every user: indexes, `python-install-mirror`, `native-tls` for an internal CA. See [uv's settings](https://docs.astral.sh/uv/reference/settings/). |

### Python versions and venvs

| Variable | Default | Description |
|---|---|---|
| `python_versions` | `[]` | Versions to install. See [Python versions](#python-versions). |
| `python_versions_source` | `uv` | The source for entries that do not name one. |
| `python_versions_dir` | `/opt/uv/python` | For `uv`, where it installs Pythons. |
| `python_versions_link_dir` | `""` | For `uv`, also put `pythonX.Y` commands here (such as `/usr/local/bin`). Empty for none, so the distribution's commands stay first on `PATH`. |
| `python_versions_package_names` | see defaults | For `repos`, the package for a version by `os_family`: `python{version}` (`python3.12`) on Red Hat and Debian, `python{nodot}` (`python312`) on SUSE. |
| `python_versions_archive_dir` | `/opt/python` | For `archive`, where versions are unpacked, one directory each. |
| `python_venvs` | `[]` | Virtual environments. See [Virtual environments](#virtual-environments). |

### Facts set by the role

| Fact | What it holds |
|---|---|
| `ansible_python_interpreter` | The interpreter the bootstrap chose. |
| `python_interpreters` | Each version in `python_versions`, mapped to its interpreter's path. |

## Python versions

Each entry is a version string, which uses `python_versions_source`, or a dict:

```yaml
python_versions:
  - "3.13"                       # from uv: the newest 3.13 patch release, kept once installed
  - version: "3.12"
    source: repos                # python3.12 from the host's repositories (python312 on SUSE)
  - version: "3.11"
    source: files                # package files from the control node
    files: "{{ query('ansible.builtin.fileglob', 'files/python311/*.rpm') }}"
    use_repos: false
  - version: "3.13.9"
    source: archive              # a python-build-standalone archive, unpacked to /opt/python/3.13.9
    archive: https://artifacts.example.internal/python/cpython-3.13.9-install_only.tar.gz
    checksum: sha256:<hex>
```

| Field | For | Description |
|---|---|---|
| `version` | all | Such as `"3.12"` or `"3.13.9"`. Quote it: YAML reads `3.10` as `3.1`. |
| `source` | all | `uv`, `repos`, `files` or `archive`. |
| `package` | `repos` | The package, if not the name from `python_versions_package_names`. |
| `files`, `use_repos` | `files` | As for the bootstrap. |
| `archive`, `checksum`, `dest` | `archive` | The file or URL, its checksum, and where to unpack it (default `<python_versions_archive_dir>/<version>`). |
| `interpreter` | all | Its path, if the default is wrong. Defaults: `/usr/bin/pythonX.Y` for `repos` and `files`, `<dest>/bin/python3` for `archive`, uv's own answer for `uv`. |

uv's Pythons come from Astral's python-build-standalone releases on GitHub, or from your mirror (`python-install-mirror` in `python_uv_config`). They and archives are not distribution packages, so the distribution's security updates do not reach them: update them by changing the version.

## Virtual environments

```yaml
python_venvs:
  - path: /opt/reporting/venv
    python: "3.13"               # a version from python_versions, a version uv can find, or a path
    packages: [requests==2.32.5]
    owner: reporting
  - path: /opt/tools/venv
    requirements: files/tools-requirements.txt   # on the control node
    exact: true                  # the venv holds exactly what the file lists
  - path: /opt/old/venv
    state: absent
```

| Field | Default | Description |
|---|---|---|
| `path` | required | Where the venv lives. A missing parent directory is made, owned by root. |
| `python` | uv's choice | A version from `python_versions` (its interpreter from `python_interpreters`), a version uv can find, or a path. A change of major or minor version makes the venv again. |
| `packages` | `[]` | Requirement strings to install. Removing one from the list does not uninstall it; use `exact`. |
| `requirements` | none | A requirements file on the control node, copied to `<path>/requirements.txt`. |
| `exact` | `false` | Hold exactly what `requirements` lists, removing anything else. Needs `requirements` and no `packages`. |
| `owner`, `group` | `root` | Who owns the venv. uv runs as the owner (through `runuser`, or `sudo` where there is no `runuser`), so every file in it is theirs. The user must exist. |
| `mode` | `0755` | The mode of `path`. |
| `state` | `present` | `absent` removes the directory. |

uv never downloads a Python for a venv: name one from `python_versions`, or one already on the host.

## Examples

### RHEL 8 hosts through Satellite, on a current control node

```yaml
- name: Give RHEL 8 a Python current ansible-core can use
  hosts: rhel8
  become: true
  gather_facts: false
  roles:
    - role: libre_devops.python   # python3.12 from AppStream, through Satellite like any package
```

### Air-gapped hosts, Python pushed from the control node

```yaml
- name: Bootstrap from RPMs brought in from outside
  hosts: isolated
  become: true
  gather_facts: false
  roles:
    - role: libre_devops.python
      vars:
        python_bootstrap_source: files
        python_bootstrap_files: "{{ query('ansible.builtin.fileglob', playbook_dir ~ '/files/rhel8-python/*.rpm') }}"
        python_uv_download_base_url: file:///srv/mirror/uv   # uv from the control node's own copy
```

### The same Python everywhere, from an internal artifact store

```yaml
- name: One Python build for every distribution
  hosts: all
  become: true
  gather_facts: false
  roles:
    - role: libre_devops.python
      vars:
        python_bootstrap_source: archive
        python_bootstrap_interpreter: /opt/python/bootstrap/bin/python3   # use it even where the host has a Python
        python_bootstrap_archive: https://artifacts.example.internal/python/cpython-3.12.16-x86_64-install_only_stripped.tar.gz
        python_bootstrap_archive_checksum: sha256:<hex>
```

### Internal package index and Python mirror for uv

```yaml
python_uv_config: |
  native-tls = true
  python-install-mirror = "https://artifacts.example.internal/python-build-standalone"

  [[index]]
  url = "https://artifacts.example.internal/api/pypi/pypi/simple"
  default = true
```

## Troubleshooting

| Symptom | What to check |
|---|---|
| `The module interpreter '/usr/bin/python3' was not found`, on Gathering Facts | The play gathers facts before the role runs. Set `gather_facts: false` and put the role first. |
| `in check mode the role cannot install one` | Installing Python is a change. Run once without `--check`; check-mode runs work after that. |
| `has no Python 3.9 or later ... cannot install one here` | The distribution is not in `python_bootstrap_packages`, or the source is missing its files or archive. Add it, or set `python_bootstrap_interpreter`. |
| `Installing python3.12 did not provide /usr/bin/python3.12` | The package exists but installs elsewhere. Set the `interpreter` in `python_bootstrap_packages`. |
| `dnf` fails with nothing to install, or missing dependencies, for `files` | The files are for another release, or a dependency is missing. Download them on a machine that matches the hosts, or set `python_bootstrap_files_use_repos: true`. |
| `Unpacking a Python archive needs tar on the host` | Install `tar`, or use `repos` or `files`. |
| A venv uses the wrong Python | `python` names a version uv found elsewhere. Name a version from `python_versions`, or a path. |

## Developing

You need [uv](https://docs.astral.sh/uv/), [just](https://github.com/casey/just) and [podman](https://podman.io/). CI runs the same recipes.

| Recipe | What it does |
|---|---|
| `just deps` | Installs the pinned Python tools (`uv.lock`) and the collections the tests use into `.ansible/`. |
| `just lint` | `yamllint`, `ansible-lint` on the production profile, and `zizmor` on the workflows. |
| `just test [scenario] [platform]` | Runs a Molecule scenario on one platform, or on all of them. `just test default rhel8`. |
| `just test-all` | Every scenario on every platform, one after another. |
| `just converge <scenario> <platform>` | Runs a scenario on one platform and leaves the container running, pass or fail. `just login` opens a shell in it, `just destroy` removes it. |
| `just live <inventory> [args]` | Runs [`examples/playbook.yml`](./examples/playbook.yml) against real hosts. |
| `just secrets` | Scans the git history with gitleaks. |
| `just platforms`, `just scenarios` | List what can be tested. |

| Scenario | What it proves |
|---|---|
| `default` | The bootstrap on every platform, from minimal images with no Python added: the right interpreter, and nothing changes on a second run. |
| `uv` | uv, two uv Python versions, `/etc/uv/uv.toml`, a venv owned by another user, an exact venv from a requirements file and a removed venv. |
| `sources` | RHEL 8 bootstrapped from pushed RPMs with its repositories off, then Python 3.11 from its repositories. Debian 12 bootstrapped from a pushed python-build-standalone archive, then Python 3.13 from another. A venv on each names its added version. |

## Releasing

1. Move the Unreleased entries in [`CHANGELOG.md`](./CHANGELOG.md) under the new version.
2. Run `just release 1.2.3`. It tags the commit and pushes the tag.
3. The Release workflow creates the GitHub release and imports the tag into Galaxy, which takes the version from the tag. It needs the `GALAXY_API_KEY` secret, which the libre-devops organisation provides. If the import fails, fix the cause and run the Release workflow by hand with the tag to import it again.

## Credits

The bootstrap's approach, reading `/etc/os-release` and installing with `raw` before any module runs, follows [robertdebock.bootstrap](https://github.com/robertdebock/ansible-role-bootstrap) (Apache-2.0). This role is written separately and adds choosing a Python by what the running ansible-core needs, and pushing Python from the control node.

## Licence

[MIT](./LICENSE).
