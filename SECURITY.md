# Security policy

## Reporting a vulnerability

Report vulnerabilities in this role privately, through [GitHub's private vulnerability reporting](https://github.com/libre-devops/ansible-role-python/security/advisories/new). Do not open a public issue.

## What the role trusts

| What | Where it comes from | How it is checked |
|---|---|---|
| Python from `repos` | The host's own repositories: the distribution's, Satellite or a mirror | The host's package manager, against the keys and repositories the host already trusts. |
| Python from `files` | Package files you put on the control node | The host's package manager checks the packages' signatures as usual. Bring them from a source you trust. |
| Python from `archive` | A python-build-standalone archive from the control node or a URL | `python_bootstrap_archive_checksum` or the version's `checksum`, when set. Set one for every URL. |
| Python from `uv` | Astral's python-build-standalone releases, or your `python-install-mirror` | uv checks each download against the checksums built into that uv release. |
| uv itself | The release archive, downloaded by the control node | The SHA-256 in `python_uv_checksums`, from the release's own `.sha256` files. |
| Packages in venvs | PyPI, or the index in `python_uv_config` | Pin versions in `packages` or the requirements file. |

Pythons from `uv` and `archive` are Astral's builds, not distribution packages, so the distribution's security updates do not reach them. Update them by changing the version.

## Pushing files

For `files` and `archive`, the role writes the files into a shell script on the control node (`files/pack.py`), runs it on the host with `ansible.builtin.script`, and deletes it from the control node afterwards. The script unpacks into a temporary directory that it removes when it exits. It runs with `become`, as the install needs root.
